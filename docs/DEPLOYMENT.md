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
.\scripts\run_web.ps1 -Rebuild   # force a fresh web build (see the PWA section)
```

Then open **http://127.0.0.1:8000/** - API docs at `/docs`.

The script does exactly:

```powershell
cd mobile; flutter build web --release --no-web-resources-cdn; cd ..
cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend auto-detects `mobile/build/web` and mounts it at `/`. Override the
location with `MLBB_WEB_ROOT=/path/to/web`.

## 2. Split hosting (static host + separate API)

Deploy `mobile/build/web` to any static host (Netlify, Vercel, GitHub Pages,
S3 + CloudFront, nginx) and point the app at the API host at build time:

```powershell
cd mobile
flutter build web --release --no-web-resources-cdn --dart-define=API_BASE_URL=https://api.example.com
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
| Web build | `flutter build web --release --no-web-resources-cdn` | from `mobile/` |
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

## 8. Publishing an app release (download page)

`/download` is a server-rendered HTML page; it reads
`releases/latest.json` **per request**, so publishing takes effect without a
restart.

```powershell
.\scripts\package_apk.ps1 -Notes "What changed`nSecond line"
```

The script:

1. runs `flutter build apk --release` in `mobile/`;
2. copies the APK to `releases/mlbb-tracker-<version>.apk`;
3. computes its SHA-256 and size;
4. reads the real `minSdk` from the artifact with `aapt2`;
5. writes `releases/latest.json` (UTF-8, no BOM).

```
releases/
├── latest.json              # manifest — version, size, sha256, notes
└── mlbb-tracker-0.8.0.apk   # served at /downloads/<file>
```

Both artifacts are **git-ignored**: the APK is a large binary, and a committed
manifest pointing at an absent APK would be a broken link. On a fresh clone
`/download` honestly says "no build published yet".

| Route | Serves |
|---|---|
| `GET /download` | the landing page |
| `GET /downloads/<file>` | the APK (`attachment`, Android MIME type) |
| `GET /api/v1/app/release` | the manifest as JSON |

### Signing (read this before distributing)

Until a release keystore is configured, Flutter signs release builds with the
**debug keys**. The manifest records this (`signed_with`) and the page labels
the build **preview**. Configure `android/key.properties` (never committed) and
a `signingConfig` in `android/app/build.gradle.kts` before publishing to a
store.

---

## 9. Installable web app (PWA)

The web build is a real PWA: it can be installed from the browser and keeps
working offline. Three source files in `mobile/web/` make it happen, and the
build copies them verbatim:

| File | Role |
|---|---|
| `manifest.json` | name, `/` start URL and scope, standalone display, icons (any + maskable), shortcuts |
| `sw.js` | the service worker - caches the shell, never the API |
| `flutter_bootstrap.js` | loads Flutter **without** its deprecated service worker, which would replace ours |

### Building

Always pass `--no-web-resources-cdn` (bundling CanvasKit locally), otherwise
the renderer is fetched from gstatic.com and the first offline launch fails:

```powershell
flutter build web --release --no-web-resources-cdn
```

### What the service worker caches

- **Precached on install**: the app shell (`index.html`, `main.dart.js`,
  bootstrap, manifest, icons) and the CanvasKit renderer, so the app paints
  with no network at all.
- **Navigations**: network-first with a cached-shell fallback.
- **Static assets**: stale-while-revalidate (fast, self-updating).
- **`/canvaskit/`**: cache-first (large, immutable per build).
- **Never cached**: everything under `/api/`, `/download`, `/downloads/`,
  `/docs`. Offline, the app shows its own error states instead of stale
  numbers - stale data presented as live would be fabricated data.

Cache names are versioned (`mlbb-shell-v1`); **bump `CACHE_VERSION` in
`sw.js` when you publish a new build** and the activate handler deletes the
old caches. Without a bump, users get the new app on their second visit.

### Installing

Install criteria (Chrome/Edge): HTTPS or localhost, a valid manifest with
192+512 icons, and an active service worker. Users can install from the
address bar, or from the **Install the web app** card on `/download`, which
drives `beforeinstallprompt` when the browser offers it and falls back to
manual instructions (Chrome Android: *Add to Home screen*; Safari iOS:
*Add to Home Screen*).

### Fonts (known gap)

`google_fonts` (Inter/Manrope) and Flutter's missing-glyph fallbacks are
fetched from fonts.gstatic.com and served from the browser's HTTP cache.
Offline-first visits fall back to system fonts - the app renders correctly,
just with different type. Bundle the TTFs in `pubspec.yaml` if pixel-identical
offline typography matters.

---

## Known limitations (honest)

- **Web is desktop-first in layout** - the UI is a mobile app shell rendered in
  a browser; it is responsive down to phone widths, which is how it is tested.
- **No server-side rendering / SEO** - the app is a Flutter canvas; the
  manifest and `/download` page are indexable, but app content is not.
- **The provider can return transient 503s** (observed from `arena.rone.dev`).
  The app shows a retry state; the API caches successful responses.
