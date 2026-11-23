# MLBB Tracker

A **Mobile Legends: Bang Bang analytics platform** — **React 19 + Vite + TypeScript** web app served by a **Laravel (PHP 8.4) API** from a single origin, with an installable PWA experience and a Flutter (Dart) Android client.

> **Live and backed by real data**: hero roster (133 heroes), win / ban / pick meta rankings with a tier-list view, recorded daily history, esports standings and verified grand-final results, a hero head-to-head comparison, a personal watchlist and Firebase-powered accounts. Nothing is ever fabricated — every number traces to a provider observation or a sourced result.

## ⬇️ Download for Windows

[![Download](https://img.shields.io/badge/Download-MLBB_Tracker_v0.12.0_(Windows)-2e7cd6?style=for-the-badge&logo=github)](https://github.com/brucequiros18/mlbbtracker/releases/download/v0.12.0/MLBB-Tracker-Windows-0.12.0.zip)

**The full working app in one zip (50 MB)** — React front end, Laravel API, SQLite database and a bundled PHP 8.4 runtime. No PHP, Composer or Node install required.

1. Unzip anywhere
2. Double-click **`START-MLBB-TRACKER.bat`**
3. Your browser opens **http://127.0.0.1:8000** — done

**🌐 Website / download page:** [brucequiros18.github.io/mlbbtracker](https://brucequiros18.github.io/mlbbtracker/) — introduction, features, similar apps, version history and the download itself.

All releases: [github.com/brucequiros18/mlbbtracker/releases](https://github.com/brucequiros18/mlbbtracker/releases)

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│ CLIENTS                                                     │
│  React 19 + Vite + TS (web/)      Flutter Android (mobile/) │
│  TanStack Query · Router ·        Riverpod · Dio            │
│  Recharts · Tailwind v4 · PWA                               │
└──────────────────────┬──────────────────────────────────────┘
                       │  /api/v1 — JSON envelope, bearer tokens
┌──────────────────────▼──────────────────────────────────────┐
│ SERVER — Laravel 13 (server/)                               │
│  • Verifies Firebase / Google ID tokens locally (RS256)     │
│  • Owns accounts, sessions, profiles (Argon2id)             │
│  • Merges + normalizes two live providers with TTL caching  │
│  • Records daily meta snapshots (Artisan command)           │
│  • Serves the SPA + download page from one origin           │
└─────────┬─────────────────────────────┬─────────────────────┘
          │                             │
  ┌───────▼────────┐          ┌─────────▼──────────┐
  │ Database        │          │ External providers │
  │ SQLite (dev),   │          │ • Rone Arena API   │
  │ Postgres-ready  │          │ • MLBBDex (CC BY-SA)│
  └─────────────────┘          └────────────────────┘
```

## Features

- **Hero roster** — 133 heroes with real in-game ids, portraits, roles and lanes.
- **Meta rankings + tier list** — win / ban / pick rates by rank tier and time window, wiki-backed **S+ → C tier badges**; switch between a grouped tier-list view and a sortable table.
- **Hero detail** — skills, ranked stats, 7-day win-rate trend chart, strong/weak relationships.
- **Hero comparison** — pick up to three heroes for a side-by-side card view with an overlaid 7-day win-rate trend (`/compare?h=a,b,c` is shareable).
- **Watchlist (Saved)** — bookmark heroes and see live tier, rank position, win rate and **7-day movement** (▲/▼), sorted by movement, with multi-select into the comparison.
- **Esports** — MPL Indonesia / Philippines / Malaysia / Cambodia standings plus **verified grand-final results** (e.g. M7 world champion Aurora Gaming PH; Bigetron's MPL ID back-to-back; Selangor Red Giants' six-peat), each linked to its source.
- **Accounts** — sign up / sign in with **Firebase email + password** (Google sign-in also supported). The ID token is verified **server-side** (RS256 against the provider's published keys, issuer, audience, expiry) — the browser never decides who the player is. The MLBB ID is **self-declared** and labelled so everywhere (`mlbbIdVerified: false`); the app password (Argon2id) only confirms profile edits.
- **PWA** — real manifest + service worker: installable from the address bar or `/download`; the shell opens offline while API calls are never cached (offline shows honest error states, never stale numbers).
- **Download page** — `/download` serves an Android APK with version, size, SHA-256 and install steps.
- **Theme** — MLBB-inspired "Land of Dawn" palette: midnight-navy arena (default), day-arena light mode, Rajdhani esports display type, electric-blue accent, legendary gold for epic moments.

## Repository layout

```
mlbb-tracker/
├── server/          Laravel 13 API (controllers, services, migrations, tests)
│   └── public/app/  the built React bundle, served at "/"
├── web/             React 19 + Vite + TypeScript + Tailwind v4 source
├── site/            GitHub Pages download website (self-contained index.html)
├── mobile/          Flutter Android client (Riverpod, Dio, FL Chart)
├── database/        PostgreSQL bootstrap schema (Laravel migrations are canonical)
├── docs/            API docs, database schema, deployment, testing report, research
├── scripts/         build_web.ps1 · run_web.ps1 · deploy_pages.ps1 · package_windows.ps1
└── releases/        published APK + latest.json (git-ignored)
```

## Quick start

### Requirements

| Tool | Version |
|---|---|
| PHP | 8.4 (with `pdo_sqlite`, `openssl`) |
| Composer | 2.x |
| Node.js + npm | 20+ / 10+ |

### Web app (one command — SPA + API on one origin)

```powershell
composer install          # inside server/ (first time)
.\scripts\run_web.ps1     # builds web/ if needed, then serves on :8000
.\scripts\run_web.ps1 -Rebuild   # force a fresh web build
```

Open **http://127.0.0.1:8000/** — the download page is at `/download`.

### Manual (two steps)

```powershell
# 1. build the React bundle and copy it into Laravel's public root
cd web ; npm install ; npm run build ; cd ..
# (scripts\build_web.ps1 does the copy for you)

# 2. serve everything with Laravel
cd server
copy .env.example .env    # then edit — see below
composer install
php artisan key:generate
php artisan migrate
php artisan serve --host 127.0.0.1 --port 8000
```

### Mobile app

```powershell
cd mobile
flutter pub get
flutter run     # Android emulator reaches the host at 10.0.2.2
```

## Environment variables (`server/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `DB_CONNECTION` | `sqlite` | `pgsql`/`mysql` in production |
| `MLBB_FIREBASE_PROJECT_ID` / `_API_KEY` / `_AUTH_DOMAIN` | *(empty)* | Firebase email+password sign-in; public values from your Firebase web config. Empty = the app reports it honestly |
| `MLBB_GOOGLE_CLIENT_ID` | *(empty)* | Optional Google sign-in (OAuth web client) |
| `MLBB_USER_SESSION_TTL_DAYS` | `30` | Sliding app-session lifetime |
| `MLBB_RONE_BASE_URL` / `MLBB_MLBBDEX_BASE_URL` | provider hosts | Data sources |
| `MLBB_ENABLE_RONE` / `MLBB_ENABLE_MLBBDEX` | `true` | Provider toggles |
| `MLBB_ENABLE_PLAYER_LOOKUP` | `false` | Consented in-game player sign-in |
| `MLBB_CACHE_TTL_RANKINGS` | `3600` | Ranking cache TTL (seconds) |

## API (v1)

```
GET  /api/v1/heroes                     roster
GET  /api/v1/heroes/rankings            meta rankings (?days&rank&sort)
GET  /api/v1/heroes/{id}                detail (skills, relations)
GET  /api/v1/heroes/{id}/trends|history 7-day trend · recorded history
GET  /api/v1/esports/{league}/standings MPL standings (id|ph|my|kh)
POST /api/v1/auth/firebase              email+password sign-in (ID token -> session)
POST /api/v1/auth/google                Google sign-in (ID token -> session)
POST /api/v1/auth/register              complete profile (username, MLBB ID, app password)
GET/PATCH /api/v1/auth/me               account · profile edits (password-confirmed)
POST /api/v1/auth/logout
GET  /api/v1/health · health/providers · health/history
GET  /api/v1/app/release · /download · /downloads/{file}
```

Every response uses one envelope (`{data, meta}`), camelCase keys and a stable error `code` — see [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md).

## Testing

```powershell
cd server
php vendor/bin/phpunit        # 57 passed / 0 failed (264 assertions)
cd ..\web
npm run lint                  # oxlint
npm run build                 # tsc -b && vite build
```

The suite is fully offline: auth tests fake the verifiers, while the **verifier suites exercise the real RS256 path** — tokens signed with a committed test key against a faked JWKS / self-signed X509 certificate (signature, issuer, audience, expiry, key-rotation refetch, HS256 forgery, upstream outages → `503`). See [docs/TESTING_REPORT.md](docs/TESTING_REPORT.md).

## Data sources & licensing

| Source | Used for | Terms |
|---|---|---|
| [Rone Arena API](https://arena.rone.dev/) | hero ids, portraits, relationships, rankings, esports | Unofficial community API; game data from Moonton public services |
| [MLBBDex](https://mlbbdex.com/) | roles, lanes, skills, tiers, patches | CC BY-SA (ML wiki) + MIT (analysis) |
| Moonton / MPL announcements, Liquipedia | verified esports results (linked per entry) | Referenced, not republished |

MLBB Tracker is an unofficial fan project, not affiliated with or endorsed by Moonton. Mobile Legends: Bang Bang is a trademark of Shanghai Moonton Technology.

## Security

- **Sign-in tokens are verified on the server** (RS256 against Google's JWKS / Firebase's certificates; issuer, audience, expiry, `email_verified`) and are never stored.
- **Sessions** are opaque bearer tokens; only their SHA-256 digest reaches the database.
- **Passwords** use Argon2id via PHP `password_hash` — never a sign-in method, never sent to Moonton.
- **Rate limiting** on the public auth (10/min per IP) and player-connect (5/min) endpoints; `429` answers the standard error envelope.
- The MLBB ID is self-declared — the API returns `mlbbIdVerified: false` everywhere so clients cannot mistake it for a fact.
- No `.env` is committed; API credentials never leave the backend. Strict CSP on the app shell.

## Documentation

| Doc | Contents |
|---|---|
| [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) | Every endpoint, envelope, error codes |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | Tables, identity model, snapshot design |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Local + production deployment, scheduler, PWA, sign-in setup |
| [docs/TESTING_REPORT.md](docs/TESTING_REPORT.md) | Test inventory and results |
| [docs/UI_UX_GUIDELINES.md](docs/UI_UX_GUIDELINES.md) | Design system |
