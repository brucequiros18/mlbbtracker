# Development Plan

Methodology: structured SDLC, milestone-gated. Each milestone is verified
before the next begins.

## Status

| # | Milestone | Status |
|---|---|---|
| 1 | Research & architecture | ✅ Complete |
| 2 | Flutter foundation (theme, nav, Home, Player Search) | ✅ Complete |
| 3 | Backend foundation (FastAPI, provider abstraction, health) | ✅ Complete |
| 4 | Player integration | ✅ **Consented sign-in**: in-game code → real profile/stats/matches/top heroes |
| 5 | Advanced analytics (rankings, hero detail, charts) | 🟡 Rankings + trend chart + **recorded history (DB snapshots, Alembic)** done; hero-comparison pending |
| 6 | Additional features (heroes DB, esports, favourites, comparison) | 🟡 Heroes + favourites + **esports standings** done; comparison pending |
| 7 | QA (automated tests, device testing, perf, security) | 🟡 Automated tests green; device pass pending |
| 8 | Release prep (APK, icon, metadata) | ⬜ Not started |

## What exists now

- **Repo**: `mobile/` (Flutter), `backend/` (FastAPI), `database/`, `docs/`.
- **Mobile**: design system, 5-tab shell (GoRouter `StatefulShellRoute`),
  Riverpod providers, Dio repositories, feature-based folders, saved heroes,
  light/dark theming, error/empty/loading states.
- **Backend**: provider adapters (Rone Arena, MLBBDex), normalization + TTL
  cache, `/heroes`, `/heroes/rankings`, `/heroes/{id}`, `/health`,
  `/players/...` (consented connect flow + `/players/me/*`), typed error
  envelope, CORS, OpenAPI.
- **Tests**: 34 backend tests (offline) + 3 widget tests; live smoke script.

## Next steps

1. **Milestone 3+ — persistence**: Alembic migrations; move `api_cache` and hero
   snapshots into Postgres; scheduled refresh job; provider health log.
2. **Milestone 5 — analytics**: ✅ 7-day win-rate trend (FL Chart) shipped.
   Remaining: longer windows, patch-over-patch deltas, hero comparison.
3. **Milestone 6 — breadth**: esports standings screens, player comparison,
   hero counter/synergy explorer.
4. **Milestone 7 — QA**: run on `Medium_Phone_API_36.1`; integration tests app↔API;
   performance/size profile; security review (CORS hardening, rate limiting).
5. **Milestone 8 — release**: app icon + metadata, signed APK, store checklist.

## Player-data decision (updated)

Player statistics are now served for **the player's own account** through a
consented sign-in: the provider sends a one-time code to the player's in-game
mailbox, the player enters it in the app, and the backend exchanges it for a
session token. No password is ever requested or stored, no auth is bypassed,
and the upstream token never leaves the server.

Anonymous lookup of *other* players remains `501 NOT_SUPPORTED` — no public
source exposes another player's stats, and the app never fabricates data.
