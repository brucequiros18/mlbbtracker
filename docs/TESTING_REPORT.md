# Testing Report

Date: **2026-11-13**. Platform: Windows 11.

Automated tests are **fully offline** (no third-party dependency). Live
integration is exercised by a separate, manually-run smoke script.

## 1. Backend — `pytest` (offline)

```
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Result: **23 passed.**

| Test file | Covers |
|---|---|
| `test_health.py` | `/health` capabilities; index metadata |
| `test_heroes.py` | list + role filter; rankings sorted; detail by slug & numeric id; relations resolved; trends sorted ascending; trends 404 envelope |
| `test_players.py` | `501 NOT_SUPPORTED` envelope; `422` digit validation |
| `test_esports.py` | standings rows + camelCase keys; rank ordering; unknown league `422` |
| `test_history.py` | rankings fetch writes snapshots; per-day idempotency; `/history` returns recorded points; empty-state note; oldest-first ordering (temp SQLite, offline) |
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

## 6. Not yet tested (honest gaps)

- **On-device run** on `Medium_Phone_API_36.1` (Milestone 7).
- **Integration tests** app↔API (contract tests) — planned.
- **Performance/size** profiling and security review — planned.
- **iOS** — project exists, not built (Android-first).

## Verdict

Backend: green (unit + live + HTTP). Mobile: analyze clean, widget test green.
No feature is claimed complete without the above evidence.
