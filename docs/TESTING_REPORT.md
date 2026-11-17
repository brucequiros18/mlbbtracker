# Testing Report

Date: **2026-11-13**. Platform: Windows 11.

Automated tests are **fully offline** (no third-party dependency). Live
integration is exercised by a separate, manually-run smoke script.

## 1. Backend — `pytest` (offline)

```
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Result: **34 passed.**

| Test file | Covers |
|---|---|
| `test_health.py` | `/health` capabilities; index metadata |
| `test_heroes.py` | list + role filter; rankings sorted; detail by slug & numeric id; relations resolved; trends sorted ascending; trends 404 envelope |
| `test_players.py` | `501 NOT_SUPPORTED` envelope; `422` digit validation |
| `test_esports.py` | standings rows + camelCase keys; rank ordering; unknown league `422` |
| `test_history.py` | rankings fetch writes snapshots; per-day idempotency; `/history` returns recorded points; empty-state note; oldest-first ordering (temp SQLite, offline) |
| `test_player_connect.py` | consented connect: code request, wrong code → 401, verify → session + hashed-key storage, profile/stats/matches/heroes mapping, disconnect revokes, numeric-id validation (temp SQLite, offline) |
| `test_providers.py` | `normalize_hero_name`; Rone Arena parsing (refs, rankings); MLBBDex parsing (catalog, detail, rankings) via `httpx.MockTransport` |

> A fixture gap briefly let the esports tests reach the live network (they
> asserted real MPL ID row counts). Fixed by overriding `get_esports_service`;
> the suite is offline again and that slip is noted here for honesty.

Providers are replaced with fakes via FastAPI dependency overrides, so tests
never hit the network and never depend on a third-party service.

## 2. Backend — live smoke (network)

```
.\.venv\Scripts\python.exe scripts\smoke_live.py
```

Result: **LIVE SMOKE OK.** Verbatim highlights:

```
rone: fetched 133 hero refs
mlbbdex: fetched 134 hero metas
rone: fetched 133 ranking rows (days=7 rank=all)
[catalog]  133 heroes; e.g. Aamon#109(Assassin), Akai#9(Tank), Aldous#64(Fighter)…
[rankings] 133 rows; top: Masha 61.1% (tier S+), Marcel 57.5% (S+), Argus 56.7% (S+)
[detail]   Khufra id=78 roles=['Tank'] lanes=['Roam']
[detail]   skills=4 strong=['Joy','Lancelot'] weak=['Fredrinn','Gloo']
[detail]   win=54.7% ban=2.1%
[player]   correctly unsupported -> NOT_SUPPORTED
```

## 2b. Backend — live trends (network)

`HeroService.trends('khufra', days=7)` → **7 real daily points**, ascending:

```
2026-11-05  win=54.70%  ban=2.09%
2026-11-08  win=54.83%  ban=2.13%
2026-11-11  win=54.99%  ban=2.04%
```

## 3. Backend — HTTP end-to-end

Uvicorn on `127.0.0.1:8077`; real requests:

| Request | Result |
|---|---|
| `GET /api/v1/health` | `200` · `status=ok`, `player=unavailable`, `player_lookup=False` |
| `GET /api/v1/heroes?role=Tank` | `200` · `count=25`, `Akai#9 roles=Tank` |
| `GET /api/v1/heroes/rankings?days=7&sort=win_rate` | `200` · top `Masha win=0.610973 tier=S+` |
| `GET /api/v1/players/123/456` | `501` (expected) |

## 4. Mobile — `flutter analyze` & `flutter test`

```
cd mobile
flutter analyze     # No issues found!
flutter test        # All tests passed! (1)
```

`test/widget_test.dart` renders the Heroes screen against a fake
`HeroRepository` (which also implements the trend interface) and asserts the
roster appears.

## 5. Browser verification (Flutter web, release build)

Built with `flutter build web --release` and served statically; driven with
Playwright (headless Chromium, 430×900):

| Scenario | Evidence |
|---|---|
| Home renders real data | Screenshot shows Masha 61.1%, Marcel 57.5%, Argus 56.7% with portraits |
| Hero detail | Portrait, roles, ranked stats, skills |
| Win-rate trend chart | FL Chart line 61.6% → 58.2% (11-05 → 11-11) |
| Console errors | **0** across all runs |
| Backend calls from browser | `/heroes/rankings`, `/heroes/88`, `/heroes/88/trends` — all 200 |

Two real defects were found and fixed by this pass:

1. **Wire-format mismatch** — the API emitted `snake_case` while Dart models
   parsed `camelCase`, so every numeric statistic rendered as `0.0%` and hero
   portraits fell back to initials. Fixed with a camelCase alias generator on
   all API schemas (`ApiModel`), verified by the wire-key check
   (`banRate, headImage, id, name, pickRate, slug, tier, winRate`).
2. **Null cast on hero detail** — the nested `rankStat` object carries only the
   three rates, but the Dart model shared with ranking rows required `id`/`name`,
   throwing `null is not a subtype of num` in release mode. Fixed by splitting
   out `HeroRankSummary` for the embedded stat.

Also fixed a `RenderFlex` overflow (5.2px) on the hero grid card surfaced by the
running app.

## 5b. Player connect flow (Flutter web, release build)

The consented sign-in flow was driven in headless Chromium against the live
backend:

| Scenario | Evidence |
|---|---|
| Connect screen renders | "Connect your account", 3-step explanation, ID/zone fields, no-password note |
| Sends the in-game code | Filling Player ID `999999999` / Zone `9999` and tapping **Send verification code** issued a real `POST /api/v1/players/connect/start` → **200**, and the UI advanced to the verification-code step |
| Console errors | **0** |
| Unauthenticated access | `GET /api/v1/players/me/profile` without a token → **401 PROVIDER_AUTH_REQUIRED** |
| Unknown player | `POST /api/v1/players/connect/start` with a bogus id → **401** with honest copy (the provider's own 500/validation bug is mapped to an auth error, not a raw 500) |

> The **final step needs the player's own inbox**: the code is delivered by
> Moonton to the connected account, so completing the sign-in requires a real
> Player ID/Zone ID and reading the code in-game. Everything up to that point
> is verified above; the dashboard itself is covered by widget tests against a
> fake provider (`player_connect_test.dart`).

## 5c. Web app — single-origin deployment

The backend serves the Flutter web build at `/`, so app and API share an origin
(`http://127.0.0.1:8000/`). Verified with Playwright against the release build:

| Scenario | Evidence |
|---|---|
| App boots from the API origin | `GET /` → `text/html`, title `MLBB Tracker`, canvas painted |
| Same-origin API calls | `GET /api/v1/heroes/rankings…` and `/api/v1/esports/id/standings` both on `127.0.0.1:8000` — no CORS preflight, no cross-origin request |
| Deep links | `/#/players` and `/#/esports` load correctly on the same origin (hash routing → no SPA rewrite rules) |
| Live data on Home | Masha 60.3%, Marcel 57.4%, Argus 56.8% |
| Security headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`; API responses `Cache-Control: no-store` |
| Console errors | **0** |

**Upstream flakiness observed:** `arena.rone.dev` intermittently returns `503`
for the esports standings endpoint (verified: fails, then succeeds on retry
with 9 rows). The app renders its retry state instead of breaking — captured
in a screenshot. This is provider-side, not an application defect.

## 5d. Phase A — data loop (recorded history, DB cache, provider health)

| Scenario | Evidence |
|---|---|
| Daily snapshot job | `scripts/install_snapshot_task.ps1` registers **"MLBB Tracker - Daily Snapshot"** (Task Scheduler, daily 03:15 local); `record_snapshot.py` verified idempotent — re-run on the same day inserts 0 rows |
| Recorded history accumulates | `hero_snapshots` holds 133 rows for each of 2026-11-14 and 2026-11-15 (two real UTC days); Masha: 60.70% → 60.26% |
| History chart states | Widget tests cover ≥2 points (line + count caption), 1 point (honest single-snapshot note, no line), 0 points ("No snapshots recorded yet") |
| DB cache tier | `cache_read`/`cache_write` unit tests: round-trip, miss, TTL expiry + purge-on-read, refresh-in-place |
| Provider health log | `record_provider_health`/`recent_provider_health` unit tests + `GET /health/history` endpoint tests (shape, empty state, limit validation) |
| Totals | **47 backend tests** (was 35), **6 widget tests** (was 3), `flutter analyze` clean |

## 5e. Download page & APK release (browser + backend)

| Scenario | Evidence |
|---|---|
| Page renders a published release | `GET /download` → 200 `text/html`; shows `v0.8.0+8`, **51.3 MB**, `Android 7.0 (API 24)`, SHA-256, preview badge, release notes, APK link |
| APK actually serves | `HEAD /downloads/mlbb-tracker-0.8.0.apk` → 200, `application/vnd.android.package-archive`, `Content-Disposition: attachment`, 53 781 724 bytes; GET returns the file |
| Path safety | `/downloads/../backend/app/main.py` and `%2e%2e%2f…` → **404**; non-`.apk` names → 404 |
| Honest empty state | With no `latest.json`, the page says "No public APK has been published" and shows **no** download link (covered by backend tests) |
| Corrupt / unsafe manifest | Non-JSON and traversal filenames in `latest.json` are ignored → empty state |
| Manifest JSON | `GET /api/v1/app/release` → 200 with version, size, sha256, notes; `404 NOT_FOUND` when unpublished |
| CSP | Page sends `default-src 'none'; style-src 'unsafe-inline'; …`; the only script is the install helper, pinned by SHA-256 (see 5f) |
| Layout | Screenshots at 1280×950 and 390×844 (buttons go full-width on phones); 0 console errors |
| App entry point | Web Home shows the "Get the Android app" card (web-only; hidden on Android) |
| Totals | **60 backend tests** (was 47), **6 widget tests**, `flutter analyze` clean |

## 5f. Installable web app (PWA, release build)

Verified in Chromium via Playwright against the single-origin deployment
(`http://127.0.0.1:8000`), with a fresh browser context each run.

| Scenario | Evidence |
|---|---|
| Manifest | `GET /manifest.json` -> 200 `application/json`; name, `/` start URL, scope, standalone, `#111318` theme/background, 4 icons (192/512 in `any` + `maskable`), 3 shortcuts |
| Icons are real | 192/512 PNGs are the generated analytics mark (not Flutter defaults); Apple touch icon 180 px, favicon 64 px |
| Worker registers | `navigator.serviceWorker.ready` -> scope `/`, state `activated`, script `/sw.js`, page **controlled** |
| Precache | `mlbb-shell-v1` holds 11 entries (shell, `main.dart.js`, bootstrap, manifest, icons); `mlbb-static-v1` holds the CanvasKit set (`canvaskit.wasm`, `chromium/canvaskit.wasm`, skwasm) |
| **Offline reload** | `context.set_offline(True)` + reload -> the app shell paints, canvas present, Home shows its honest error state ("Cannot reach the MLBB Tracker server… Try again") - see `pwa_offline.png` |
| API is never cached | Offline, `/api/v1/heroes/rankings` fails with `ERR_INTERNET_DISCONNECTED` and is **not** answered from cache - no stale numbers presented as live |
| CanvasKit offline | Bundled locally (`--no-web-resources-cdn`); `/canvaskit/chromium/canvaskit.js` + `.wasm` served from cache offline |
| `/download` install card | "Install the web app" card renders with manual instructions; the button stays hidden until `beforeinstallprompt` fires (headless Chromium never fires it) |
| CSP hash | The page's single inline script is pinned by SHA-256 in `script-src` (no `'unsafe-inline'`), with `manifest-src`/`worker-src`; verified by a backend test that re-hashes the served script |
| Escaping | A hostile manifest (`<script>`, `<img onerror>`, event handler in `channel`) is escaped / sanitised - verified by test |
| Regression guards | `test_pwa_assets.py`: manifest fields, icon files and PNG dimensions, shortcut routes, worker precache list + API exclusions, index registers `sw.js` (not `flutter_service_worker.js`), bootstrap has no `serviceWorkerSettings` |
| Totals | **69 backend tests** (was 60), **6 widget tests**, `flutter analyze` clean |

**Known gap:** offline, missing-glyph fallback fonts and `google_fonts` assets
are unavailable from gstatic.com; the app falls back to system fonts and the
console logs repeated font-fetch warnings (154-181 per offline run). Rendering
and navigation are unaffected. See `docs/DEPLOYMENT.md` section 9.

## 6. Not yet tested (honest gaps)

- **On-device run** on `Medium_Phone_API_36.1` (Milestone 7).
- **Full live sign-in** with a real account (requires the player's in-game
  mailbox — see 5b).
- **Integration tests** app↔API (contract tests) — planned.
- **Performance/size** profiling and security review — planned.
- **iOS** — project exists, not built (Android-first).

## Verdict

Backend: green (unit + live + HTTP). Mobile: analyze clean, 3 widget tests green.
No feature is claimed complete without the above evidence.
