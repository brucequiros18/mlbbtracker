# Database Schema

Target: **PostgreSQL (Supabase)**. Schema is defined in
[`database/schema.sql`](../database/schema.sql).

> **Status.** The running backend currently serves from providers + an
> in-process TTL cache; it does not yet require a database. This schema is the
> agreed target for Milestone 3+, where scheduled snapshots, saved players and
> caching move into Postgres. No fabricated data is seeded.

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
| `users` | optional accounts (Supabase Auth `uuid`) | `id`, `email`, `created_at` |
| `heroes` | hero catalog | `id` (in-game id), `name`, `slug`, `roles[]`, `lanes[]`, `tier` |
| `hero_statistics` | hero win/ban/pick snapshots | `hero_id`, `rank`, `days`, `win_rate`, `ban_rate`, `pick_rate`, `recorded_at` |
| `player_snapshots` | player stats over time (only if a source appears) | `player_id`, `zone_id`, `rank`, `total_matches`, `wins`, `losses`, `win_rate`, `kda`, `mvp_count`, `recorded_at` |
| `match_history` | per-match rows (same caveat) | `match_id`, `player_id`, `zone_id`, `hero_id`, `result`, `kills`, `deaths`, `assists`, `duration`, `game_mode`, `played_at`, `raw_data` |
| `tracked_players` | players a user follows | `user_id`, `player_id`, `zone_id` |
| `favorites` | favourite heroes per user | `user_id`, `hero_id` |
| `recent_searches` | recent player searches | `user_id`, `player_id`, `zone_id`, `searched_at` |
| `api_cache` | provider response cache | `cache_key` (unique), `provider`, `payload jsonb`, `expires_at` |
| `provider_health` | provider availability log | `provider`, `status`, `checked_at`, `latency_ms` |

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
