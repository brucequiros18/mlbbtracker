# Development Plan

Methodology: structured SDLC, milestone-gated. Each milestone is verified
before the next begins.

## Status

| # | Milestone | Status |
|---|---|---|
| 1 | Research & architecture | ✅ Complete |
| 2 | Flutter foundation (theme, nav, Home, Player Search) | ✅ Complete |
| 3 | Backend foundation (FastAPI, provider abstraction, health) | ✅ Complete |
| 4 | Player integration | ⛔ Blocked (no permitted source) — UI + provider ready |
| 5 | Advanced analytics (rankings, hero detail, charts) | 🟡 Core done; historical snapshots pending DB |
| 6 | Additional features (heroes DB, esports, favourites, comparison) | 🟡 Heroes + favourites done; esports/comparison pending |
| 7 | QA (automated tests, device testing, perf, security) | 🟡 Automated tests green; device pass pending |
| 8 | Release prep (APK, icon, metadata) | ⬜ Not started |

## What exists now

- **Repo**: `mobile/` (Flutter), `backend/` (FastAPI), `database/`, `docs/`.
- **Mobile**: design system, 5-tab shell (GoRouter `StatefulShellRoute`),
  Riverpod providers, Dio repositories, feature-based folders, saved heroes,
  light/dark theming, error/empty/loading states.
- **Backend**: provider adapters (Rone Arena, MLBBDex), normalization + TTL
  cache, `/heroes`, `/heroes/rankings`, `/heroes/{id}`, `/health`,
  `/players/...` (501), typed error envelope, CORS, OpenAPI.
- **Tests**: 13 backend tests (offline) + 1 widget test; live smoke script.

## Next steps

1. **Milestone 3+ — persistence**: Alembic migrations; move `api_cache` and hero
   snapshots into Postgres; scheduled refresh job; provider health log.
2. **Milestone 5 — analytics**: historical win-rate timeline chart (FL Chart),
   patch-over-patch deltas, hero trend screens.
3. **Milestone 6 — breadth**: esports standings screens, player comparison,
   hero counter/synergy explorer.
4. **Milestone 7 — QA**: run on `Medium_Phone_API_36.1`; integration tests app↔API;
   performance/size profile; security review (CORS hardening, rate limiting).
5. **Milestone 8 — release**: app icon + metadata, signed APK, store checklist.

## Player-data decision (standing)

Player statistics remain blocked: the only source requires signing in as the
player. Per the brief, we keep the UI and provider interface ready, return an
explicit `NOT_SUPPORTED`, and never fabricate data. Revisit only if a permitted,
consented source appears.
