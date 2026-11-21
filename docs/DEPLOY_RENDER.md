# Deploying the public URL (Render + GitHub Pages)

GitHub Pages hosts the **React app** (static files only — it cannot run
PHP). The **Laravel API** deploys to [Render](https://render.com)'s free
tier from this same GitHub repo. Together they give the app a live public
URL:

| Piece | Host | URL |
|---|---|---|
| React app | GitHub Pages | `https://brucequiros18.github.io/mlbbtracker/` |
| Laravel API | Render | `https://<your-service>.onrender.com` |

---

## Step 1 — Deploy the API on Render (~10 minutes, free)

1. Go to <https://dashboard.render.com/select-repo> and sign in with GitHub.
2. Choose **Blueprint** and select the `brucequiros18/mlbbtracker` repo —
   Render reads [`render.yaml`](../render.yaml) automatically.
3. For the `APP_KEY` prompt, either let Render generate one or paste any
   `base64:...` key.
4. Press **Apply**. Render builds the Docker image (PHP + extensions +
   Composer + the React build) and boots it.
5. When it's live, Render shows the service URL — something like
   `https://mlbbtracker.onrender.com`. Verify: open
   `https://<your-service>.onrender.com/api/v1/health` → `status: ok`.

Notes:
- The free tier cold-starts after ~15 idle minutes (first request takes
  ~50 s to wake). It also runs `php artisan migrate` on every boot; SQLite
  storage is ephemeral on free, so accounts reset on redeploy — use a paid
  disk or Postgres for persistence.
- To sign in with Firebase from the Render origin, also add the Render URL
  to **Firebase console → Authentication → Settings → Authorized domains**.

## Step 2 — Point GitHub Pages at the API (~2 minutes)

```powershell
.\scripts\deploy_pages.ps1 -ApiBase https://<your-service>.onrender.com
```

This builds the React app with `VITE_API_BASE` set to the Render origin,
fixes the `/mlbbtracker/` paths, adds the `404.html` SPA fallback and
force-pushes the `gh-pages` branch.

## Step 3 — Enable GitHub Pages (once)

1. Open <https://github.com/brucequiros18/mlbbtracker/settings/pages>
2. **Source**: Deploy from a branch · **Branch**: `gh-pages` · **Folder**:
   `/ (root)` · **Save**.
3. Wait ~1 minute for the first deployment.

## Step 4 — Open the app

**https://brucequiros18.github.io/mlbbtracker/** — full app, live data,
Firebase sign-in, shareable comparison links. If a data call fails, check
that the Render service is awake and that
`MLBB_CORS_ALLOWED_ORIGINS` (render.yaml) contains the exact Pages origin.

## Re-deploying

- **Push to `main`** → Render auto-rebuilds the API (autoDeploy: true).
- **Any theme/feature change to `web/`** → re-run `deploy_pages.ps1`.
