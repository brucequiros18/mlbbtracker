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
  `/heroes/rankings`, `/heroes/{id}`, `/heroes/{id}/trends`,
  `/players/{player_id}/{zone_id}`.
- Typed error envelope, CORS, OpenAPI, structured logging, `/docs`.
- Tests: 13 offline `pytest` tests + live smoke script.
- `database/schema.sql` (PostgreSQL/Supabase) and `DATABASE_SCHEMA.md`.

### Notes
- Player statistics are intentionally **not** served: no permitted public source
  exposes them. The app shows a clear explanation and never fabricates data.
- MLBB Tracker is unofficial and not affiliated with Moonton.

## [0.5.0] — 2026-11-15

### Added — Milestone 4: consented player tracking (real player stats)
- **Backend**: `PlayerSessionProvider` interface + Rone Arena adapter for the
  provider's own consent flow — `POST /user/auth/send-vc` (one-time code to the
  player's in-game mailbox) → `POST /user/auth/login` → `data.jwt`.
- New endpoints: `POST /players/connect/start`, `POST /players/connect/verify`,
  `POST /players/disconnect`, `GET /players/me/{profile,stats,matches,heroes}`.
  The upstream JWT never leaves the backend; the app holds an opaque session
  key (stored server-side by SHA-256 hash).
- New `player_sessions` table + Alembic migration `3dbed8e9151e`.
- `GET /players/{id}/{zone}` still returns `501 NOT_SUPPORTED` — other players'
  stats are not publicly available, and nothing is fabricated.
- Provider quirks handled: the provider's 500-on-invalid-login is mapped to
  `401 PROVIDER_AUTH_REQUIRED` with honest copy.
- **Mobile**: Players tab rebuilt as a connect flow (ID/zone → in-game code →
  connected dashboard) with real stats grid (matches, wins, WR, avg score, MVP,
  win streak), recent matches (hero, K/D/A, KDA, MVP flag, win/loss, relative
  time) and top heroes; pull-to-refresh, disconnect with confirmation.
- `401` added to the client's error taxonomy.
- Dashboard polls every 60s while open ("Live tracking") so a finished game
  appears without a manual refresh; pull-to-refresh still works.
- Tests: 34 backend (11 new, offline) + 2 new widget tests.

## [0.4.0] — 2026-11-14

### Added — Milestone 5 (part): persistence + recorded history
- Backend: SQLAlchemy 2 + Alembic (`hero_snapshots` table, migration
  `16af8bfd4fb2`). Dev DB is SQLite (`MLBB_DATABASE_URL` switches to Supabase
  Postgres; models/migrations shared).
- Every fresh 7-day rankings fetch records daily hero snapshots (one per hero
  per UTC day, idempotent; failures never break the API).
- New `GET /api/v1/heroes/{identifier}/history` — our own observation history
  (`sources` empty by design; honest empty-state note until data accumulates).
- `backend/scripts/record_snapshot.py` for scheduled refreshes; first live run
  recorded 133 heroes (Masha 60.70% WR, rank #1).
- Tests: 23 backend tests (5 new, offline on temp SQLite).

## [0.3.0] — 2026-11-14

### Added — Milestone 6: esports standings
- Backend: `EsportsStandingsProvider` + Rone Arena adapter; cached
  `GET /api/v1/esports/{league}/standings` for MPL ID/PH/MY/KH.
- Mobile: esports feature (model, repository, providers, screen) with league
  chips, team logos and colour-coded game differential; reachable from Home and
  via `/#/esports` deep link.
- Router switched to hash URLs so the app can be hosted statically.
- Error copy: UI now shows friendly messages instead of `toString()`.
- Tests: 18 backend tests.

## [0.2.0] — 2026-11-14

### Added — Flutter web target
- `web/` platform added; `ApiConfig.baseUrl` is now platform-aware
  (Android emulator → `10.0.2.2`, web/desktop → `localhost`), still overridable
  with `--dart-define=API_BASE_URL`.

### Fixed — wire format & hero detail parsing
- API schemas now emit **camelCase** (`winRate`, `headImage`, …) to match the
  Dart models; previously every statistic rendered as `0.0%`.
- Split `HeroRankSummary` out of `HeroRankStat` for the embedded detail stat,
  fixing a `null is not a subtype of num` crash on hero detail.
- Fixed a 5.2px `RenderFlex` overflow on the hero grid card.

### Added — Milestone 5: hero trend analytics
- Backend: `HeroTrendProvider` interface + Rone Arena adapter; cached
  `GET /api/v1/heroes/{id}/trends?days=` returning an ascending daily timeline.
- Mobile: `HeroTrendPoint` model, `HeroRepository.heroTrends()`, and a
  win-rate line chart (`fl_chart`) on the hero detail screen. Trend failures
  degrade to a caption instead of breaking the page.
- Tests: 15 backend tests (was 13); `flutter analyze` clean.
