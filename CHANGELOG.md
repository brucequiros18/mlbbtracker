# Changelog

All notable changes are documented here. Format follows Keep a Changelog;
versions use Semantic Versioning.

## [0.1.0] — 2026-11-13

### Added — Milestone 1: Research & architecture
- Live verification of MLBB data providers (Rone Arena, MLBBDex) with captured
  sample responses in `docs/research/samples/`.
- Data availability matrix, limitations/risks, and implementation strategy
  (`docs/RESEARCH_MILESTONE_1.md`).
- Repository structure and documentation set.

### Added — Milestone 2: Flutter application
- Design system ("Competitive Minimalism"): `AppPalette`, `AppSpacing`,
  `AppRadius`, `AppTypography`, `AppTheme` (dark + light).
- Reusable widgets: `AppCard`, `AppPrimaryButton`, `AppTextField`, `StatTile`,
  `SectionHeader`, `HeroAvatar`/`RoleTag`, `LoadingView`/`EmptyView`/`ErrorView`.
- 5-tab shell via GoRouter `StatefulShellRoute`; Home, Heroes (grid + detail),
  Ranks, Players, Saved screens.
- Riverpod providers, Dio repositories, typed models; on-device recent searches
  and favourite heroes (`shared_preferences`); light/dark theme toggle.

### Added — Milestone 3: FastAPI backend
- Provider abstraction (`HeroIdentityProvider`, `HeroMetaProvider`,
  `HeroRankingProvider`, `PlayerProvider`) + factory.
- Adapters: Rone Arena (ids, portraits, rankings, relations), MLBBDex
  (roles, lanes, skills, tiers, patches); `NullPlayerProvider` → `NOT_SUPPORTED`.
- `HeroService` merge/normalize with in-process TTL cache; attribution envelope.
- Endpoints: `/api/v1/health`, `/health/providers`, `/heroes`,
  `/heroes/rankings`, `/heroes/{id}`, `/players/{player_id}/{zone_id}`.
- Typed error envelope, CORS, OpenAPI, structured logging, `/docs`.
- Tests: 13 offline `pytest` tests + live smoke script.
- `database/schema.sql` (PostgreSQL/Supabase) and `DATABASE_SCHEMA.md`.

### Notes
- Player statistics are intentionally **not** served: no permitted public source
  exposes them. The app shows a clear explanation and never fabricates data.
- MLBB Tracker is unofficial and not affiliated with Moonton.
