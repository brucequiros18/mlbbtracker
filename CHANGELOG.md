# Changelog

All notable changes are documented here. Format follows Keep a Changelog;
versions use Semantic Versioning.

## [Unreleased]

### Fixed — Firebase sign-in was unreachable behind the app's own CSP
- The strict Content-Security-Policy refused the connection to Firebase's
  Identity Toolkit (`identitytoolkit.googleapis.com`), so email + password
  sign-in, sign-up and password reset always failed with
  `auth/network-request-failed` — "Could not reach Firebase" — regardless of
  the actual connection. `connect-src` now allows the two Firebase
  Authentication endpoints (`identitytoolkit` + `securetoken` for ID-token
  refresh); Google sign-in endpoints stay allowed and the `/download` page
  policy remains closed. Covered by `tests/Feature/CspTest.php` (3 cases).

### Changed — Sign-in / registration UI rebuilt
- `EmailAuthForm`: tabbed sign-in / create-account / reset instead of buried
  text links, inline validation on blur (email format, password length,
  confirmation match), a live requirement checklist while creating an account,
  a password visibility toggle, `aria-invalid` / `aria-describedby` wiring and
  `role="alert"` on the form error.
- `ProfileSetup`: the same blur validation for username, MLBB ID and app
  password using the exact patterns the server publishes in
  `GET /api/v1/auth/config`, plus the same checklist and toggle.
- The shared `Field` component now associates its label with the input
  (`htmlFor`), shows field-level errors/hints and supports blur validation.
- The router basename now comes from an explicit `VITE_ROUTER_BASENAME`
  build variable (set by `deploy_pages.ps1`, empty for single-origin builds)
  instead of `import.meta.env.BASE_URL` — Vite's asset base (`/app/`) is not
  the document base, and deriving the basename from it broke routes on the
  single-origin deployment.

## [0.12.0] — 2026-11-21

### Added — Full working Windows package + download website
- **Self-contained Windows package** (`MLBB-Tracker-Windows-0.12.0.zip`,
  52,809,640 bytes / 50.4 MB, SHA-256
  `f0384f26e0f9c2e94a30094dfbc1f8b3e60a6a3916a80795b9009e868cf97f98`):
  bundled PHP 8.4.28 runtime + Laravel API + built React SPA + empty SQLite.
  `START-MLBB-TRACKER.bat` migrates, serves and opens the app at
  `http://127.0.0.1:8000` — no installs, no admin rights, no dependencies.
- Smoke-tested end to end: extract → migrate → serve → health check OK.
- AI-generated app icon processed into the full PWA icon set; project
  documentation (`docs/PROJECT_EXPLANATION_SCRIPT.docx`) and the 18-slide
  presentation added.
- **Download website** (`site/index.html`, published to GitHub Pages):
  introduction, feature overview, problem/solution, similar-apps comparison,
  version history and the download card with the real checksum, size and date.

### Changed — GitHub Pages layout
- Pages now serves the **landing page at the root** and the **React SPA under
  `/mlbbtracker/app/`** (`scripts/deploy_pages.ps1`).
- The SPA builds with `--base=/mlbbtracker/app/` and `deploy_pages.ps1` sets
  `VITE_ROUTER_BASENAME=/mlbbtracker/app/` so `BrowserRouter` matches deep
  links such as `/app/compare?h=masha,argus` instead of falling to the
  router's 404.
- The root `404.html` is the SPA index plus a redirect that folds unknown paths
  under the basename (React Router v7 renders nothing when a URL does not start
  with the basename), keeping the SPA-fallback trick working on Pages.

## [0.11.0] — 2026-11-20

### Changed — Backend migration: FastAPI → Laravel
- The Python FastAPI backend is replaced by a **Laravel (PHP 8.4)** API in
  `server/`, keeping the exact same `/api/v1` JSON contract (`{data, meta}`
  envelope, camelCase keys, stable error `code`s).
- Same real providers (Rone Arena + MLBBDex), same merge/normalize behaviour,
  same attribution envelope — no data is fabricated.
- **App password hashing upgraded: scrypt -> Argon2id** via PHP
  `password_hash()` (`App\Support\Passwords`).
- Google ID tokens are verified locally with `openssl_verify` + a cached JWKS
  fetch (RS256; issuer, audience, expiry, `email_verified`), TTL reduced to
  5 minutes with a second refetch on unknown key ids for smoother key
  rotation.
- Migrations (SQLite for dev, Postgres-ready): `users`, `user_sessions`,
  `player_sessions`, `hero_snapshots`, `api_cache`, `provider_health`.
- Routes split: `routes/api.php` (versioned JSON API) and `routes/web.php`
  (single-origin `/download` + React SPA fallback).

### Added — Web client migration: Flutter web → React + Vite
- **React 19 + TypeScript + Vite + Tailwind** app in `web/`, keeping the
  "Competitive Minimalism" dark-first design.
- TanStack Query for data fetching/caching, React Router for navigation,
  Recharts for trend/history charts.
- 5-tab shell (Home, Heroes, Ranks, Players, Saved), hero detail with trend
  chart, esports standings, Google Identity Services sign-in, profile setup,
  account card, player connect flow and live dashboard.
- PWA manifest + service worker + icons; built bundle is served by Laravel
  from a single origin (`server/public/app/`).
- `scripts/build_web.ps1` builds React and copies it into the Laravel public
  root; `scripts/run_web.ps1 -Rebuild` serves API + web together.

### Fixed
- PHPUnit auth suite now fully green: **23 passed / 0 failed** (was 4/19).
  Test tokens satisfy the `credential min:20` rule, data providers pass
  positionally, password assertions use Argon2id-aware `Passwords::verify()`.

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

## [0.10.0] — 2026-11-17

### Added — Google-only accounts
- **Google is the only way to register or sign in.** There is no password
  login, no email login and no anonymous account. The Players tab walks
  through three steps, each shown only when the previous one is done: Google
  sign-in, profile setup, then the consented in-game connect flow.
- **`POST /api/v1/auth/google`** takes the ID token from Google Identity
  Services and verifies it **locally**: RS256 signature against Google's JWKS
  (cached, refetched on key rotation), issuer, audience (our own client ID),
  expiry and `email_verified`. The stable `sub` claim is the account key; the
  token itself is never stored. JWKS outages are a `503`, not a fake success.
- **Profile setup** (`POST /api/v1/auth/register`) collects the username, the
  MLBB ID and an **app password**. The username is unique, case-insensitive.
  The MLBB ID is **self-declared**: it is stored as typed, never checked
  against Moonton, and every response says `mlbbIdVerified: false`. The app
  password is app-only — an **Argon2id** hash (PHP `password_hash`), never
  sent to Moonton and never used to sign in; it only confirms profile edits.
- **Sessions** (`GET/PATCH /api/v1/auth/me`, `POST /api/v1/auth/logout`):
  opaque bearer tokens, only their SHA-256 digest stored, 30-day sliding
  expiry, one row per sign-in. An expired or revoked token signs the app out
  instead of showing a profile it can no longer prove.
- **Honest configuration state**: `GET /api/v1/auth/config` reports whether
  Google sign-in is configured. With no `MLBB_GOOGLE_CLIENT_ID` the app shows
  "Google sign-in is not configured" and the API answers `503
  GOOGLE_NOT_CONFIGURED` — it never offers a button that cannot work.
- **Web** renders the official Google Identity Services button (GIS only
  permits sign-in from UI it draws itself); **Android** uses the native
  account picker. Either way the backend is the only place the token is
  verified.
- New tables `users` and `user_sessions` (Alembic revision `9c1a7f42b6d8`;
  `Base.metadata.create_all` also adds them to an existing dev database at
  startup).
- App version `0.10.0+10`.
- Tests: **105 backend** (36 new: sign-in, registration, sessions, profile
  edits, password hashing, and the real verifier against a local RSA key),
  **12 widget tests** (6 new: sign-in, profile setup, validation, sign-out).

### Changed
- The Players tab is gated on an app account; signing out also disconnects the
  game link, so statistics are no longer visible on that device.
- The connect step now states that the MLBB Tracker profile is not linked to
  Moonton and that the provider token stays on the backend.

## [0.9.0] — 2026-11-16

### Added — installable web app (PWA)
- **Real web app manifest** (`mobile/web/manifest.json`): app name, `/` start
  URL and scope, standalone display, theme/background `#111318`, 192/512 icons
  in both `any` and `maskable` variants, and shortcuts to Heroes, Esports and
  Leaderboards.
- **Generated icon set** (`scripts/generate_web_icons.py`, Pillow): the
  analytics mark on the accent gradient — 192/512 + maskable, a 180 px Apple
  touch icon and a 64 px favicon. No Flutter defaults left.
- **Service worker** (`mobile/web/sw.js`): precaches the app shell and
  CanvasKit, network-first navigations with a cached-shell fallback,
  stale-while-revalidate for static assets, cache-first `/canvaskit/`, and
  versioned caches cleaned on activate. **API and release routes are never
  cached** — offline the app shows its honest error states instead of stale
  numbers.
- **Offline-capable build**: `--no-web-resources-cdn` bundles CanvasKit, so
  the renderer no longer depends on gstatic. `scripts/run_web.ps1` uses it.
- **Custom bootstrap** (`mobile/web/flutter_bootstrap.js`) that does not load
  Flutter's deprecated service worker — it would replace ours on the same
  scope and then unregister itself.
- **`/download` → "Install the web app"**: an install button driven by
  `beforeinstallprompt`, manual instructions for Chrome/Edge, Chrome Android
  and Safari iOS, and an "installed" state under `display-mode: standalone`.
- **CSP hardened, not loosened**: the page's single inline script is pinned by
  SHA-256 (no `script-src 'unsafe-inline'`), with `manifest-src`/`worker-src`
  allowed for the manifest and worker, and `img-src 'self' data:` for icons.
- **HTML escaping** of every manifest-derived string on `/download` (version,
  notes, checksum, signing note, channel) plus a sanitised badge class.
- App version `0.9.0+9`; APK republished as **0.9.0+9, 51.3 MB, Android 7.0+
  (API 24)**, debug-signed and still labelled preview.
- Tests: **69 backend** (9 new: install card, CSP hash, escaping, manifest,
  icons, worker guards), 6 widget tests.

### Fixed
- Service-worker cache lookups now ignore `Vary`: responses carry
  `Vary: Origin` from the CORS middleware, which made module-script requests
  miss the cache and fail offline.

## [0.8.0] — 2026-11-16

### Added — download page & APK release pipeline
- **`GET /download`** — a plain server-rendered HTML landing page (no
  JavaScript, no Flutter canvas, indexable): app icon, version, size,
  SHA-256, release date, minimum Android, release notes, three-step install
  guide, and a "use the web app" alternative. Responsive, dark/light aware,
  styled to the design system.
- **`GET /downloads/<file>`** — serves the APK with the Android MIME type and
  `Content-Disposition: attachment`; strict `*.apk` filename allowlist (path
  traversal and other extensions return 404). GET and HEAD supported.
- **`GET /api/v1/app/release`** — the release manifest as JSON
  (`404 NOT_FOUND` until something is published).
- **`scripts/package_apk.ps1`** — one command: `flutter build apk --release`,
  copy into `releases/`, compute SHA-256/size, read the real `minSdk` from the
  artifact with `aapt2`, write `releases/latest.json` (UTF-8, no BOM).
- **Honest states**: with no manifest the page says "no build published yet"
  and shows no link; a corrupt or unsafe manifest is ignored.
- **Home (web only)**: "Get the Android app" card linking to `/download`.
- App version aligned to the project: `0.8.0+8`.
- First published build: **0.8.0+8, 51.3 MB, Android 7.0+ (API 24)** — debug
  signed, labelled **preview** on the page and in the manifest.
- Docs: `releases/README.md`, deployment "Publishing a release" section, API
  reference. Tests: **60 backend** (13 new: page states, MIME/headers, path
  safety, manifest endpoint), 6 widget tests.

## [0.7.0] — 2026-11-16

### Added — Phase A: the data loop
- **Scheduled snapshots**: `scripts/install_snapshot_task.ps1` registers a
  Windows Task Scheduler job (daily 03:15 local) running the idempotent
  `backend/scripts/record_snapshot.py` (one row per hero per UTC day); cron
  line documented in `docs/DEPLOYMENT.md`.
- **Recorded history in the app**: hero detail now shows an **"Our
  Observations"** section (distinct colour + caption) fed by
  `GET /heroes/{id}/history` — the backend's own daily snapshots, never
  blended with the provider's trend. Honest states: 0 points → "No snapshots
  recorded yet", 1 point → single-snapshot note (no line drawn).
- **DB-backed cache tier**: new `api_cache` table (migration
  `264514ec345c`) is the cold tier behind the in-process TTL cache — a backend
  restart no longer re-fetches the full catalog/rankings upstream.
- **Provider health log**: every live provider call is recorded to the new
  `provider_health` table (status, status code, latency, error code) via a
  sink wired at startup; visible at `GET /api/v1/health/history` (newest
  first, `limit` 1–200). Outages like the intermittent upstream 503s now
  leave a trace.
- Tests: **47 backend** (cache tier, health log, `/health/history`, limit
  validation), **6 widget tests** (history chart states).

## [0.6.0] — 2026-11-15

### Added — deployable web app (single origin)
- FastAPI now serves the Flutter web build at `/` when `mobile/build/web`
  exists (override with `MLBB_WEB_ROOT`), so app + API share one origin:
  **no CORS configuration, one deployable unit**.
- `scripts/run_web.ps1` — one command: build (if needed) and serve on `:8000`.
- Web client defaults to the **origin it is served from**; `--dart-define=
  API_BASE_URL=…` still points it at a separate API host.
- Proper web metadata: title/description/Open Graph, app-themed PWA manifest
  (`#111318` / `#8B7CFF`), branded loading splash, `color-scheme` support.
- Baseline security headers (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`) and `Cache-Control: no-store` on API
  responses.
- `MLBB_CORS_ORIGINS` accepts a comma-separated list (no JSON needed).
- Health payload now reports `player_connection` and `web_app` capabilities;
  API index moved to `/api/meta` (`/` is the app).
- `docs/DEPLOYMENT.md` — hosting options, env vars, production checklist,
  nginx sample, known limitations.
- Tests: 35 backend (root route now serves the app or the JSON index).

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
