# Deployment — Web App

MLBB Tracker ships as a **single-origin web app**: the React (Vite) build and
the Laravel API are served by one process, so the browser never makes a
cross-origin request and no CORS configuration is required.

```
Browser ──► http://host:8000/            → React app (static files from server/public/app)
        ──► http://host:8000/api/v1/...  → Laravel → provider adapters
```

---

## 1. Local (one command)

```powershell
.\scripts\run_web.ps1            # builds if needed, then serves on :8000
.\scripts\run_web.ps1 -Rebuild   # force a fresh web build (see the PWA section)
.\scripts\run_web.ps1 -Port 8080 # serve on another port
```

Then open **http://127.0.0.1:8000/** - download page at `/download`.

The script does exactly:

```powershell
# 1. build the React bundle and copy it into Laravel's public root
cd web; npm install; npm run build; cd ..
# web/dist/* -> server/public/app/*
# 2. serve everything with Laravel
cd server; php artisan serve --host 127.0.0.1 --port 8000
```

For development of the web app itself you can also run Vite's dev server on
:5173 (`cd web; npm run dev`); it proxies `/api/*` and `/download` to Laravel
on :8000 (`web/vite.config.ts`).

## 2. Requirements

| Tool | Version | Used for |
|---|---|---|
| PHP | 8.4 (with `pdo_sqlite`, `openssl`) | Laravel API |
| Composer | 2.x | PHP dependencies |
| Node.js | 20+ | React build tooling |
| npm | 10+ | JS dependencies |

First-time setup:

```powershell
cd server
composer install
copy .env.example .env        # then edit (see section 3)
php artisan key:generate
php artisan migrate           # creates all tables (SQLite by default)
cd ..\web
npm install
```

## 3. Configuration

Laravel settings live in `server/.env` (never committed). The MLBB-specific
values are read by `server/config/mlbb.php`.

| Variable | Default | Purpose |
|---|---|---|
| `DB_CONNECTION` | `sqlite` | `pgsql`/`mysql` in production (`DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD`) |
| `MLBB_WEB_ROOT` | auto-detected | directory holding the React build (`server/public/app`) |
| `MLBB_RELEASES_DIR` | auto-detected (`<repo>/releases`) | published APKs + `latest.json` |
| `MLBB_RONE_BASE_URL` | `https://arena.rone.dev/api` | provider host |
| `MLBB_MLBBDEX_BASE_URL` | `https://mlbbdex.com/api/v1` | provider host |
| `MLBB_ENABLE_RONE` / `MLBB_ENABLE_MLBBDEX` | `true` | provider toggles |
| `MLBB_ENABLE_PLAYER_LOOKUP` | `false` | master switch for the consented player source |
| `MLBB_HTTP_TIMEOUT` | `15` | provider request timeout (seconds) |
| `MLBB_GOOGLE_CLIENT_ID` | *(empty)* | OAuth 2.0 **web** client ID; empty = sign-in honestly reports "not configured" |
| `MLBB_USER_SESSION_TTL_DAYS` | `30` | sliding app-session lifetime |
| `MLBB_CACHE_TTL_RANKINGS` | `3600` | ranking cache TTL (seconds) |

## 4. Production checklist

1. **Database** — set `DB_CONNECTION=pgsql` plus host/port/database/user/password
   and run the migrations:
   ```powershell
   cd server
   php artisan migrate
   ```
   Install/enable the PHP `pgsql` extension first. `database/schema.sql`
   remains a Supabase bootstrap; Laravel migrations are canonical.
2. **App key** — `php artisan key:generate` (never reuse a key across
   environments).
3. **Config/route caches** — `php artisan config:cache` and
   `php artisan route:cache` after deploying; `php artisan cache:clear` when
   Google reports verification errors (JWKS refresh).
4. **Security headers** — the API sets `X-Content-Type-Options`,
   `X-Frame-Options`, `Referrer-Policy` and `Permissions-Policy`; API
   responses are `no-store`.
5. **Session storage** — the upstream player token is stored in the database
   **unencrypted** (development default). Encrypt it at rest (or keep it in a
   secrets manager) before exposing the API publicly.
6. **Rate limiting** - not implemented yet. Put a reverse proxy in front of
   `/api/v1/players/connect/*` and `/api/v1/auth/*` before public exposure.
7. **Google sign-in** - set `MLBB_GOOGLE_CLIENT_ID` and add the exact
   production origin to the OAuth client's authorized JavaScript origins
   (section 10). Never commit a real `.env`.
8. **Provider attribution** - MLBBDex data is CC BY-SA; the attribution is
   carried in every API response envelope and surfaced in the app.

## 5. Reverse proxy (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name mlbb.example.com;

    root /srv/mlbb-tracker/server/public;
    index index.php;

    location /app/ { try_files $uri =404; }          # React assets (hashed names)
    location /downloads/ { try_files $uri =404; }    # APK artifacts

    location / {
        # SPA fallback + API + downloads go through Laravel
        try_files /app/index.html @laravel;
    }

    location @laravel {
        include fastcgi_params;
        fastcgi_pass unix:/run/php/php8.4-fpm.sock;  # or 127.0.0.1:9000
        fastcgi_param SCRIPT_FILENAME $realpath_root/index.php;
        fastcgi_param DOCUMENT_ROOT $realpath_root;
    }
}
```

## 6. Processes

| Process | Command | Notes |
|---|---|---|
| API + web | `php artisan serve --host 0.0.0.0 --port 8000` | dev only |
| API + web (prod) | PHP-FPM + nginx (section 5) | or `php artisan octane:start` |
| Web build | `npm run build` (in `web/`) | output copied to `server/public/app` |
| Snapshot job | `php artisan mlbb:record-snapshot` | schedule daily (section 7) |
| Migrations | `php artisan migrate` | run once per deploy |

## 7. Daily snapshot job

The recorded-history charts only grow if something snapshots the meta once a
day. `php artisan mlbb:record-snapshot` (in `server/`) fetches the live 7-day
rankings and writes **one row per hero per UTC day** — idempotent, so re-runs
and retries never duplicate data.

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
15 3 * * * cd /srv/mlbb-tracker/server && php artisan mlbb:record-snapshot >> storage/logs/snapshot.log 2>&1
```

> Prefer a UTC-hour shortly after Moonton's daily reset for consistent
> day-over-day deltas.

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
└── mlbb-tracker-0.10.0.apk  # served at /downloads/<file>
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

## 9. Installable web app (PWA)

The React build is a real PWA: it can be installed from the browser and keeps
working offline. The source files live in `web/public/` and Vite copies them
verbatim into the bundle:

| File | Role |
|---|---|
| `manifest.webmanifest` | name, `/` start URL and scope, standalone display, icons (any + maskable) |
| `sw.js` | the service worker - caches the app shell, never the API |
| `icon-192/512.png`, `icon-maskable-*.png`, `apple-touch-icon.png` | install icons |

### Building

```powershell
.\scripts\build_web.ps1 -Clean   # fresh Vite build, copied to server/public/app
```

### What the service worker caches

- **Precached on install**: the app shell (`index.html`, JS/CSS bundles,
  manifest, icons), so the app paints with no network at all.
- **Navigations**: network-first with a cached-shell fallback.
- **Static assets**: hashed Vite output, cacheable indefinitely.
- **Never cached**: everything under `/api/`, `/download`, `/downloads/`.
  Offline, the app shows its own error states instead of stale numbers -
  stale data presented as live would be fabricated data.

**Bump the cache version in `web/public/sw.js` when you publish a new build**
so the activate handler deletes the old caches. Without a bump, users get the
new app on their second visit.

### Installing

Install criteria (Chrome/Edge): HTTPS or localhost, a valid manifest with
192+512 icons, and an active service worker. Users can install from the
address bar, or from the **Install the web app** card on `/download`, which
drives `beforeinstallprompt` when the browser offers it and falls back to
manual instructions (Chrome Android: *Add to Home screen*; Safari iOS:
*Add to Home Screen*).

## 10. Google sign-in (the only credential)

Accounts use **Google sign-in only** — there is no password login and no email
login. The backend verifies each Google ID token **locally** (RS256 signature
against Google's published JWKS, issuer, audience, expiry, `email_verified`)
and keeps only the stable `sub` claim; the token itself is never stored.

Setup:

1. Create an OAuth 2.0 **Web** client in Google Cloud Console.
2. Put its client ID in `server/.env` as `MLBB_GOOGLE_CLIENT_ID=…`.
3. Under *Authorized JavaScript origins* add every origin the app is served
   from — for local development `http://localhost:5173`,
   `http://127.0.0.1:5173`, `http://localhost:8000` and
   `http://127.0.0.1:8000`; in production, your real origin. GIS refuses to
   render from an origin that is not on this list.
4. The web app loads Google Identity Services and renders the official
   button; the browser POSTs the resulting `credential` to
   `POST /api/v1/auth/google`, where the Laravel backend verifies it.

Without a configured client ID the API answers `503 GOOGLE_NOT_CONFIGURED`
and the app says so honestly instead of showing a button that cannot work.
The MLBB ID collected at registration is **self-declared** — it is stored as
typed, never checked against Moonton, and every account payload carries
`mlbbIdVerified: false`. The app password (Argon2id, PHP `password_hash`) is
app-only: it confirms profile edits and is never a sign-in method.
