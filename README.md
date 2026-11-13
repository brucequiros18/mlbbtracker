# MLBB Tracker

A Mobile Legends: Bang Bang analytics platform — Flutter (Dart) mobile app + Python FastAPI backend.

> **Status: Milestone 1 complete, Milestones 2–3 in progress.** The hero/meta
> analytics are live and backed by real data. Per-player statistics are **not**
> available from any permitted public source and are shown as such — the app
> never fabricates player data. See [docs/RESEARCH_MILESTONE_1.md](docs/RESEARCH_MILESTONE_1.md).

## What works today (real data)

- **Hero roster** — 133 heroes with real in-game ids, portraits, roles and lanes.
- **Meta rankings** — real win / ban / pick rates by rank tier and time window, with wiki-backed tiers.
- **Hero detail** — skills, ranked stats, and strong/weak relationships resolved from real hero ids.
- **Original UI** — dark-first "Competitive Minimalism" design system, 5-tab navigation, saved heroes, theming.
- **Player search** — full UI + validation, but the backend returns an explicit `501 NOT_SUPPORTED` because no honest source exists (documented, never faked).

## Repository layout

```
mlbb-tracker/
├── mobile/        Flutter app (Dart, Riverpod, GoRouter, Dio, FL Chart)
├── backend/       FastAPI service (provider adapters, caching, tests)
├── database/      PostgreSQL schema
├── docs/          Plans, API documentation, schema, UI/UX, testing report, research
└── README.md
```

## Quick start

### Backend

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

### Mobile

```powershell
cd mobile
flutter pub get
# Android emulator reaches the host backend at 10.0.2.2 (the default).
flutter run
# Physical device on your LAN:
flutter run --dart-define=API_BASE_URL=http://<your-ip>:8000
```

## Testing

```powershell
cd backend ; .\.venv\Scripts\python.exe -m pytest      # 13 tests, offline
cd mobile  ; flutter analyze ; flutter test            # no issues, 1 test
```

Automated tests never touch the network. Adapters are verified against realistic
payloads with an `httpx.MockTransport`; a separate live smoke script exercises the
real providers.

## Data sources & licensing

| Source | Used for | Terms |
|---|---|---|
| [Rone Arena API](https://arena.rone.dev/) | hero ids, portraits, relationships, rankings | Unofficial community API; game data from Moonton public services |
| [MLBBDex](https://mlbbdex.com/) | roles, lanes, skills, tiers, patches | CC BY-SA (ML wiki) + MIT (analysis) |

MLBB Tracker is an unofficial fan project, not affiliated with or endorsed by
Moonton. Mobile Legends: Bang Bang is a trademark of Shanghai Moonton Technology.

## Security

API credentials (if ever needed) stay on the backend in `.env`. No `.env` is
committed; see `.env.example`. The app never asks for Moonton passwords and never
bypasses provider authentication.
