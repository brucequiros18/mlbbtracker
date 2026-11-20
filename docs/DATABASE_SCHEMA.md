# Database Schema

Target: **PostgreSQL (Supabase)**. Schema is defined in
[`database/schema.sql`](../database/schema.sql).

> **Status.** The backend persists data through **SQLAlchemy 2 + Alembic**
> (`backend/migrations/`; revisions `16af8bfd4fb2` heroes, `3dbed8e9151e`
> player sessions, `264514ec345c` api cache + provider health, `9c1a7f42b6d8`
> app accounts). Development runs on SQLite (`backend/mlbb_tracker.db`,
> git-ignored); production points `MLBB_DATABASE_URL` at a Supabase Postgres
> URL — same models, same migrations (install `psycopg2-binary` for Postgres).
> **Live tables:** `hero_snapshots`, `player_sessions`, `api_cache`,
> `provider_health`, `users`, `user_sessions`.
> The remaining tables below are design targets for future increments
> (favorites still live on-device). No fabricated data is seeded.

## Design principles

- Normalized columns for everything queried; `JSONB` only for provider raw
  payloads (`api_cache.payload`, `match_history.raw_data`).
- Timestamps are `timestamptz` in **UTC**.
- Foreign keys with `ON DELETE CASCADE` for user-owned rows.
- Indexes on the columns we actually filter/sort by.
- Row Level Security for user-owned tables (`users`, `tracked_players`,
  `favorites`, `recent_searches`); public game data is world-readable.
- Minimal personal data — only what the product needs.

## Tables

| Table | Purpose | Key columns |
|---|---|---|
| `users` | app accounts, created by Google sign-in | `id`, `google_sub` (unique), `email`, `email_verified`, `username` (unique), `mlbb_id`, `password_hash`, `created_at`, `last_login_at` |
| `user_sessions` | signed-in app sessions | `token_hash` (unique, SHA-256), `user_id` FK, `expires_at`, `last_seen_at` |
| `heroes` | hero catalog | `id` (in-game id), `name`, `slug`, `roles[]`, `lanes[]`, `tier` |
| `hero_statistics` | hero win/ban/pick snapshots | `hero_id`, `rank`, `days`, `win_rate`, `ban_rate`, `pick_rate`, `recorded_at` |
| `player_snapshots` | player stats over time (only if a source appears) | `player_id`, `zone_id`, `rank`, `total_matches`, `wins`, `losses`, `win_rate`, `kda`, `mvp_count`, `recorded_at` |
| `match_history` | per-match rows (same caveat) | `match_id`, `player_id`, `zone_id`, `hero_id`, `result`, `kills`, `deaths`, `assists`, `duration`, `game_mode`, `played_at`, `raw_data` |
| `tracked_players` | players a user follows | `user_id`, `player_id`, `zone_id` |
| `favorites` | favourite heroes per user | `user_id`, `hero_id` |
| `recent_searches` | recent player searches | `user_id`, `player_id`, `zone_id`, `searched_at` |
| `api_cache` | provider response cache | `cache_key` (unique), `provider`, `payload jsonb`, `expires_at` |
| `provider_health` | provider availability log | `provider`, `status`, `checked_at`, `latency_ms` |

## Notes on the account tables

Google is the only credential. `users.google_sub` is the stable `sub` claim of
a verified Google ID token, so it — not the email — is the identity key. No
Google token is stored.

`users.mlbb_id` is **self-declared**: it is typed in by the player, stored as
given, and never verified against Moonton, so `UserAccount.mlbbIdVerified` is
always `false`. `users.password_hash` is an app-only **Argon2id** hash (PHP
`password_hash`, format `$argon2id$v=19$m=…,t=…,p=…$salt$hash`); it is never
sent to Moonton and is not a sign-in method — it only confirms profile edits
(`PATCH /api/v1/auth/me`).

`user_sessions` mirrors the consented player-session pattern: the app holds an
opaque bearer token and the database stores only its SHA-256 digest. Sessions
expire after 30 days and slide on use (at most one refresh per hour). Deleting
a user cascades to their sessions.

## Notes on the player tables

`player_snapshots`, `match_history`, `tracked_players` and `recent_searches`
exist so the roadmap is unblocked the day a **permitted, consented** player
source is added. Until then they stay empty — the API returns `NOT_SUPPORTED`
and nothing writes fabricated rows. Recent searches currently live on-device
(`shared_preferences`), which is why the schema also supports a server copy for
signed-in users.

## Migrations

- Author migrations with **Alembic** (`backend/`), `database/migrations/` holds
  the generated SQL.
- `database/schema.sql` is the canonical bootstrap for a fresh Supabase project.
