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

**Phase A — data loop: ✅ complete (0.7.0).** Daily snapshots are scheduled
(Windows Task Scheduler / cron), the app renders the recorded history as a
separate "Our Observations" chart, `api_cache` is a live DB-backed cold tier,
and every provider call is logged to `provider_health` (visible at
`/health/history`).

## What exists now

- **Repo**: `mobile/` (Flutter), `backend/` (FastAPI), `database/`, `docs/`,
  `scripts/`.
- **Mobile**: design system, 5-tab shell (GoRouter `StatefulShellRoute`),
  Riverpod providers, Dio repositories, feature-based folders, saved heroes,
  light/dark theming, error/empty/loading states, consented player connect +
  live dashboard, hero detail with provider trend **and** recorded-history
  charts.
- **Backend**: provider adapters (Rone Arena, MLBBDex), normalization +
  two-tier cache (in-process TTL + `api_cache` table), `/heroes`,
  `/heroes/rankings`, `/heroes/{id}`, `/heroes/{id}/trends`,
  `/heroes/{id}/history`, `/health`, `/health/providers`,
  `/health/history`, `/players/...` (consented connect flow + `/players/me/*`),
  typed error envelope, CORS, security headers, OpenAPI, single-origin web
  serving.
- **Ops**: `scripts/record_snapshot.py` + `scripts/install_snapshot_task.ps1`
  (daily idempotent snapshot), `scripts/run_web.ps1`.
- **Tests**: 47 backend tests (offline) + 6 widget tests; live smoke script.

**Download page: ✅ complete (0.8.0).** `/download` serves a real APK with
version, size, SHA-256, notes and install steps; `scripts/package_apk.ps1`
builds and publishes it; the page degrades to an honest "not published yet"
state when nothing exists.

## Next steps

1. **Milestone 5 — analytics**: hero comparison (2–3 heroes side by side),
   counter/synergy explorer (`/academy/heroes/{id}/builds`, `/counters`).
2. **Milestone 7 — QA**: run on `Medium_Phone_API_36.1` (software GPU flags);
   integration tests app↔API; performance/size profile; security review
   (CORS hardening, rate limiting, token encryption at rest).
3. **Milestone 8 — release**: app icon + metadata, release keystore +
   signed APK, store checklist.

## Player-data decision (updated)

Player statistics are now served for **the player's own account** through a
consented sign-in: the provider sends a one-time code to the player's in-game
mailbox, the player enters it in the app, and the backend exchanges it for a
session token. No password is ever requested or stored, no auth is bypassed,
and the upstream token never leaves the server.

Anonymous lookup of *other* players remains `501 NOT_SUPPORTED` — no public
source exposes another player's stats, and the app never fabricates data.
