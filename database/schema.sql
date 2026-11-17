-- MLBB Tracker — PostgreSQL (Supabase) schema
-- Bootstrap a fresh database. Migrations are managed with Alembic.
-- Timestamps are UTC (timestamptz). Public game data is world-readable;
-- user-owned rows are protected by Row Level Security.

create extension if not exists "pgcrypto";

-- ── App accounts (Google is the only credential) ─────────────────────────
-- `google_sub` is the stable `sub` claim of a verified Google ID token.
-- `mlbb_id` is self-declared and never verified against Moonton.
-- `password_hash` is an app-only salted scrypt hash: never a login method.
create table if not exists users (
    id              bigint generated always as identity primary key,
    google_sub      text not null unique,
    email           text not null,
    email_verified  boolean not null default false,
    google_name     text,
    picture_url     text,
    username        text unique,
    mlbb_id         text,
    password_hash   text,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    last_login_at   timestamptz not null default now()
);
create unique index if not exists idx_users_username_lower on users (lower(username));

-- ── App sessions (one row per Google sign-in) ───────────────────────────
-- Only the SHA-256 digest of the opaque bearer token is stored.
create table if not exists user_sessions (
    id           bigint generated always as identity primary key,
    token_hash   text not null unique,
    user_id      bigint not null references users (id) on delete cascade,
    created_at   timestamptz not null default now(),
    expires_at   timestamptz not null,
    last_seen_at timestamptz not null default now()
);
create index if not exists idx_user_sessions_user on user_sessions (user_id);

-- ── Heroes ───────────────────────────────────────────────────────────────────
create table if not exists heroes (
    id          integer primary key,              -- real in-game hero id
    name        text not null,
    slug        text not null unique,
    roles       text[] not null default '{}',
    lanes       text[] not null default '{}',
    specialty   text[] not null default '{}',
    head_image  text,
    tier        text,
    updated_at  timestamptz not null default now()
);
create index if not exists idx_heroes_name on heroes (lower(name));

-- ── Hero statistics snapshots ────────────────────────────────────────────────
create table if not exists hero_statistics (
    id          bigint generated always as identity primary key,
    hero_id     integer not null references heroes (id) on delete cascade,
    rank        text not null default 'all',
    days        smallint not null default 7,
    win_rate    numeric(6,5) not null,
    ban_rate    numeric(6,5) not null,
    pick_rate   numeric(6,5) not null,
    recorded_at timestamptz not null default now()
);
create index if not exists idx_hero_stats_lookup
    on hero_statistics (hero_id, rank, days, recorded_at desc);

-- ── Player sessions (consented sign-in) ───────────────────────────────────────
-- One row per connected account. `provider_token` holds the upstream JWT and
-- must never be exposed to clients; the app receives an opaque session key
-- whose SHA-256 hash is stored in `session_hash`.
create table if not exists player_sessions (
    id             bigint generated always as identity primary key,
    session_hash   text not null unique,              -- sha256 of the app session key
    provider_token text not null,                     -- upstream JWT (server-side only)
    role_id        text not null,
    zone_id        text not null,
    ign            text,
    created_at     timestamptz not null default now(),
    last_seen_at   timestamptz not null default now()
);
create index if not exists idx_player_sessions_hash on player_sessions (session_hash);

-- ── Player snapshots (only populated if a permitted source appears) ──────────
create table if not exists player_snapshots (
    id            bigint generated always as identity primary key,
    player_id     text not null,
    zone_id       text not null,
    rank          text,
    total_matches integer,
    wins          integer,
    losses        integer,
    win_rate      numeric(6,5),
    kda           numeric(6,2),
    mvp_count     integer,
    recorded_at   timestamptz not null default now(),
    unique (player_id, zone_id, recorded_at)
);
create index if not exists idx_player_snapshots_lookup
    on player_snapshots (player_id, zone_id, recorded_at desc);

-- ── Match history (same caveat as player snapshots) ──────────────────────────
create table if not exists match_history (
    id         bigint generated always as identity primary key,
    match_id   text not null,
    player_id  text not null,
    zone_id    text not null,
    hero_id    integer references heroes (id),
    result     text,                                -- win | loss
    kills      integer,
    deaths     integer,
    assists    integer,
    duration   integer,                             -- seconds
    game_mode  text,
    played_at  timestamptz,
    raw_data   jsonb,
    unique (match_id, player_id, zone_id)
);
create index if not exists idx_match_history_player
    on match_history (player_id, zone_id, played_at desc);

-- ── Tracked players (follow) ─────────────────────────────────────────────────
create table if not exists tracked_players (
    id         bigint generated always as identity primary key,
    user_id    bigint not null references users (id) on delete cascade,
    player_id  text not null,
    zone_id    text not null,
    created_at timestamptz not null default now(),
    unique (user_id, player_id, zone_id)
);

-- ── Favourites ───────────────────────────────────────────────────────────────
create table if not exists favorites (
    id         bigint generated always as identity primary key,
    user_id    bigint not null references users (id) on delete cascade,
    hero_id    integer not null references heroes (id) on delete cascade,
    created_at timestamptz not null default now(),
    unique (user_id, hero_id)
);

-- ── Recent searches ──────────────────────────────────────────────────────────
create table if not exists recent_searches (
    id          bigint generated always as identity primary key,
    user_id     bigint not null references users (id) on delete cascade,
    player_id   text not null,
    zone_id     text not null,
    searched_at timestamptz not null default now(),
    unique (user_id, player_id, zone_id)
);

-- ── Provider response cache ──────────────────────────────────────────────────
create table if not exists api_cache (
    id         bigint generated always as identity primary key,
    cache_key  text not null unique,
    provider   text not null,
    payload    jsonb not null,
    expires_at timestamptz not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_api_cache_expires on api_cache (expires_at);

-- ── Provider health log ──────────────────────────────────────────────────────
create table if not exists provider_health (
    id          bigint generated always as identity primary key,
    provider    text not null,
    status      text not null,                       -- up | down
    latency_ms  integer,
    checked_at  timestamptz not null default now()
);

-- ── Row Level Security (user-owned tables) ───────────────────────────────────
alter table tracked_players  enable row level security;
alter table favorites        enable row level security;
alter table recent_searches  enable row level security;

create policy if not exists tracked_players_owner on tracked_players
    using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy if not exists favorites_owner on favorites
    using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy if not exists recent_searches_owner on recent_searches
    using (auth.uid() = user_id) with check (auth.uid() = user_id);
