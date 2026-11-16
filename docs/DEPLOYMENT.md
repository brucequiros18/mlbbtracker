# Deployment — Web App

MLBB Tracker ships as a **single-origin web app**: the Flutter web build and
the FastAPI API are served by one process, so the browser never makes a
cross-origin request and no CORS configuration is required.

```
Browser ──► http://host:8000/            → Flutter web app (static files)
        ──► http://host:8000/api/v1/...  → FastAPI → provider adapters
```

---

## 1. Local (one command)

```powershell
.\scripts\run_web.ps1            # builds if needed, then serves on :8000
.\scripts\run_web.ps1 -Rebuild   # force a fresh `flutter build web --release`
```

Then open **http://127.0.0.1:8000/** — API docs at `/docs`.

The script does exactly:

```powershell
cd mobile; flutter build web --release; cd ..
cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend auto-detects `mobile/build/web` and mounts it at `/`. Override the
location with `MLBB_WEB_ROOT=/path/to/web`.

## 2. Split hosting (static host + separate API)

Deploy `mobile/build/web` to any static host (Netlify, Vercel, GitHub Pages,
S3 + CloudFront, nginx) and point the app at the API host at build time:

```powershell
cd mobile
flutter build web --release --dart-define=API_BASE_URL=https://api.example.com
```

On the API host, allow the web origin:

```powershell
$env:MLBB_CORS_ORIGINS = "https://app.example.com"   # comma-separated list
```

Without the override the web build calls **the origin it is served from** —
which is why the single-origin setup needs no configuration at all.

> The app uses **hash URLs** (`/#/heroes`, `/#/esports`), so no SPA rewrite
> rules are needed on the static host.

## 3. Configuration

All settings are environment variables prefixed `MLBB_` (or a `.env` file in
`backend/`).

| Variable | Default | Purpose |
|---|---|---|
| `MLBB_DATABASE_URL` | `sqlite:///./mlbb_tracker.db` | Postgres/Supabase URL in production |
| `MLBB_WEB_ROOT` | auto-detected | directory holding the Flutter web build |
| `MLBB_CORS_ORIGINS` | `*` | comma-separated allowed origins (split hosting) |
| `MLBB_RONE_BASE_URL` | `https://arena.rone.dev/api` | provider host (mirror: `arena.fastapicloud.dev`) |
| `MLBB_MLBBDEX_BASE_URL` | `https://mlbbdex.com/api/v1` | provider host |
| `MLBB_ENABLE_RONE` / `MLBB_ENABLE_MLBBDEX` | `true` | provider toggles |
| `MLBB_ENVIRONMENT` | `development` | reported by `/api/v1/health` |
| `MLBB_CACHE_TTL_RANKINGS` | `3600` | ranking cache TTL (seconds) |

## 4. Production checklist

1. **Database** — set `MLBB_DATABASE_URL` to your Supabase/Postgres URL and
   run the migrations:
   ```powershell
   cd backend
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```
   Install a driver first: `pip install psycopg2-binary`.
2. **CORS** — set `MLBB_CORS_ORIGINS` to the exact web origin.
3. **Security headers** — the API sets `X-Content-Type-Options`, `X-Frame-Options`,
   `Referrer-Policy` and `Permissions-Policy`; API responses are `no-store`.
4. **Session storage** — the upstream player token is stored in the database
   **unencrypted** (development default). Encrypt it at rest (or keep it in a
   secrets manager) before exposing the API publicly, and move the on-device
   session key to platform secure storage.
5. **Rate limiting** — not implemented yet. Put a reverse proxy in front of
   `/api/v1/players/connect/*` before public exposure.
6. **Provider attribution** — MLBBDex data is CC BY-SA; the attribution is
   carried in every API response envelope and surfaced in the app.

## 5. Reverse proxy (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name mlbb.example.com;

    root /srv/mlbb-tracker/mobile/build/web;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs { proxy_pass http://127.0.0.1:8000; }
}
```

## 6. Processes

| Process | Command | Notes |
|---|---|---|
| API | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | from `backend/` |
| Web build | `flutter build web --release` | from `mobile/` |
| Snapshot job | `python scripts/record_snapshot.py` | schedule daily (see below) |
| Migrations | `alembic upgrade head` | run once per deploy |

---

## 7. Daily snapshot job

The recorded-history charts only grow if something snapshots the meta once a
day. `backend/scripts/record_snapshot.py` fetches the live 7-day rankings and
writes **one row per hero per UTC day** — idempotent, so re-runs and retries
never duplicate data.

### Windows (Task Scheduler) — one command

```powershell
.\scripts\install_snapshot_task.ps1 -RunNow     # install + first snapshot
.\scripts\install_snapshot_task.ps1 -Uninstall  # remove
```

Creates task **"MLBB Tracker - Daily Snapshot"** (default 03:15 local, runs
whether or not you are logged on, no password stored, restarts twice on
failure, 15-minute execution limit).

### Linux / macOS (cron)

```cron
15 3 * * * cd /srv/mlbb-tracker/backend && .venv/bin/python scripts/record_snapshot.py >> snapshot.log 2>&1
```

> Prefer a UTC-hour shortly after Moonton's daily reset for consistent
> day-over-day deltas.

---

## Known limitations (honest)

- **Web is desktop-first in layout** — the UI is a mobile app shell rendered in
  a browser; it is responsive down to phone widths, which is how it is tested.
- **CanvasKit is fetched from gstatic.com** by default. For a fully offline or
  CSP-restricted deployment, build with `--wasm` and self-host the renderer, or
  bundle canvaskit locally.
- **No server-side rendering / SEO** — the app is a Flutter canvas; metadata
  and an installable manifest are provided, but content is not indexable.
- **The provider can return transient 503s** (observed from `arena.rone.dev`).
  The app shows a retry state; the API caches successful responses.
