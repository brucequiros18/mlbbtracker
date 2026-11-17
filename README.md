# MLBB Tracker

A Mobile Legends: Bang Bang analytics platform — Flutter (Dart) app (Android + **web**) + Python FastAPI backend.

> **Status: Milestones 1–6 done.** Hero/meta analytics, esports standings and
> **your own player statistics** (via a consented in-game code sign-in) are
> live and backed by real data. Nothing is ever fabricated — see
> [docs/RESEARCH_MILESTONE_1.md](docs/RESEARCH_MILESTONE_1.md).

## What works today (real data)

- **Hero roster** — 133 heroes with real in-game ids, portraits, roles and lanes.
- **Meta rankings** — real win / ban / pick rates by rank tier and time window, with wiki-backed tiers.
- **Hero detail** — skills, ranked stats, 7-day win-rate trend chart, strong/weak relationships.
- **Recorded history** — daily snapshots the backend itself observes, served from the database.
- **Esports** — MPL Indonesia / Philippines / Malaysia / Cambodia standings, schedules and match details.
- **Player tracking** — connect **your own** account with a one-time code from your in-game mailbox; real profile, stats (wins, win rate, avg score, MVP count, win streak), match history with K/D/A and W/L, and top heroes. Live-polling every 60 s.
- **Web app** - the Flutter web build is served by the API from a single origin: one URL, no CORS setup. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
- **Installable + offline (PWA)** - a real manifest, generated icons and a service worker: install it from the browser (own window, home-screen icon) and the app shell still launches with no connection. API calls are never cached, so offline you get honest error states, not stale numbers.
- **Download page** - `/download` serves a real Android APK with version, size, SHA-256 and install steps (`.\scripts\package_apk.ps1` publishes it), plus an "Install the web app" card. Honest "no build published yet" state until an APK exists.
- **Original UI** — dark-first "Competitive Minimalism" design system, 5-tab navigation, saved heroes, theming.

## Repository layout

```
mlbb-tracker/
├── mobile/        Flutter app (Dart, Riverpod, GoRouter, Dio, FL Chart)
├── backend/       FastAPI service (provider adapters, caching, DB, tests)
├── database/      PostgreSQL schema
├── docs/          Plans, API docs, schema, UI/UX, testing report, research, deployment
├── scripts/       run_web.ps1 — build + serve the web app
└── README.md
```

## Quick start

### Web app (one command — app + API on one origin)

```powershell
.\scripts\run_web.ps1            # builds if needed, then serves on :8000
```

Open **http://127.0.0.1:8000/** — API docs at `/docs`, Android download and
web-app installation at `/download`. In Chrome, the address bar's install icon
(or that page's install card) adds the app to your desktop or home screen.

### Backend only

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API docs: http://127.0.0.1:8000/docs
```

Live provider smoke test (network):

```powershell
.\.venv\Scripts\python.exe scripts\smoke_live.py
```

### Mobile app

```powershell
cd mobile
flutter pub get

# Android emulator reaches the host backend at 10.0.2.2 (the default).
flutter run

# Web dev server (debug build is slow to first paint; prefer the release build):
flutter run -d chrome --web-port 8090

# Physical device on your LAN:
flutter run --dart-define=API_BASE_URL=http://<your-ip>:8000
```

## Testing

```powershell
cd backend ; .\.venv\Scripts\python.exe -m pytest      # 35 tests, offline
cd mobile  ; flutter analyze ; flutter test             # no issues, 3 tests
```

Automated tests never touch the network. Adapters are verified against realistic
payloads with an `httpx.MockTransport`; a separate live smoke script exercises the
real providers.

## Data sources & licensing

| Source | Used for | Terms |
|---|---|---|
| [Rone Arena API](https://arena.rone.dev/) | hero ids, portraits, relationships, rankings, esports, player self-sign-in | Unofficial community API; game data from Moonton public services |
| [MLBBDex](https://mlbbdex.com/) | roles, lanes, skills, tiers, patches | CC BY-SA (ML wiki) + MIT (analysis) |

MLBB Tracker is an unofficial fan project, not affiliated with or endorsed by
Moonton. Mobile Legends: Bang Bang is a trademark of Shanghai Moonton Technology.

## Security

API credentials (if ever needed) stay on the backend in `.env`. No `.env` is
committed; see `.env.example`. The app never asks for Moonton passwords and never
bypasses provider authentication: the player signs in with a one-time code sent
to their own in-game mailbox, and the resulting token stays server-side (the
device holds only an opaque session key).
