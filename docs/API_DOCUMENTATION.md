# API Documentation

Two layers: **our API** (what the Flutter app calls) and the **external
providers** it aggregates. All external endpoints were verified live on
2026-11-13; raw responses live in `docs/research/samples/`.

---

## A. MLBB Tracker API (our backend)

Base URL: `http://<host>:8000/api/v1` · OpenAPI: `/docs`, `/openapi.json`

**Envelope.** Lists return `{"data": [...], "meta": {...}}`; items return
`{"data": {...}, "meta": {...}}`. Errors return
`{"status":"error","code":"…","message":"…","details"?: "…","timestamp":"…"}`.

### `GET /health`
Capability + provider summary.
```json
{"status":"ok","providers":{"hero_identity":"rone_arena","hero_meta":"mlbbdex","ranking":"rone_arena","player":"unavailable"},
 "capabilities":{"hero_catalog":true,"hero_detail":true,"hero_rankings":true,"player_lookup":false},
 "cache":{"entries":0,"expired":0}}
```

### `GET /health/providers`
Live reachability probe of each provider (`up`/`down`) with a hero count.

### `GET /health/history?limit=50`
The **recorded** provider call log — what actually happened, as persisted by
previous requests (no upstream calls are made). Every live provider request is
appended with its status, latency and error code, so outages (e.g. the
intermittent 503s from `arena.rone.dev`) leave a trace instead of being silent.
```json
{"status":"ok","count":2,"events":[
  {"provider":"rone_arena","endpoint":"/api/heroes/rank","status":"ok",
   "statusCode":200,"latencyMs":412,"errorCode":null,"checkedAt":"2026-11-15T21:07:42+00:00"},
  {"provider":"rone_arena","endpoint":"/api/esports/id/standings","status":"error",
   "statusCode":503,"errorCode":"http_503","checkedAt":"2026-11-15T21:07:50+00:00"}]}
```
`limit` ∈ `1..200` (default `50`), newest first.

### `GET /api/v1/app/release`
The published Android release manifest — the same document the `/download`
page is rendered from.
```json
{"data":{"version":"0.8.0+8","version_name":"0.8.0","build":8,"channel":"preview",
 "file":"mlbb-tracker-0.8.0.apk","size_bytes":53781724,"sha256":"730f…",
 "released_at":"2026-11-16","min_android":"7.0 (API 24)",
 "signed_with":"debug keys - preview build; configure a release keystore before store distribution",
 "notes":["…"]},
 "meta":{"sources":[]}}
```
`404 NOT_FOUND` until a release has been packaged — a missing build is never
fabricated.

### `GET /download` (HTML, outside `/api/v1`)
Server-rendered landing page for the Android build: version, size, SHA-256,
release notes, install steps, and an "Install the web app" card. It is plain
server-rendered HTML (no Flutter canvas), so it loads instantly and is
indexable; the only script is a small install helper whose SHA-256 is pinned in
the page's `Content-Security-Policy`. When no release is published it says so
and offers the web app instead.

The PWA assets are served from the web build root: `/manifest.json`, `/sw.js`,
`/icons/*`, `/apple-touch-icon.png` and `/canvaskit/*` (bundled renderer).

### `GET /downloads/<filename>` (outside `/api/v1`)
Serves the APK with `Content-Type: application/vnd.android.package-archive`
and `Content-Disposition: attachment`. Only plain `*.apk` names inside the
releases directory are served — traversal and other extensions return `404`.

### `GET /heroes`
Query: `role` (e.g. `Tank`), `lane` (e.g. `Roam`). Returns `HeroSummary[]`:
```json
{"id":78,"name":"Khufra","slug":"khufra","roles":["Tank"],"lanes":["Roam"],
 "head_image":"https://…","tier":"A+"}
```

### `GET /heroes/rankings`
Query: `days` ∈ `1|3|7|15|30` (default `7`), `rank` ∈
`all|epic|legend|mythic|honor|glory`, `sort` ∈ `win_rate|ban_rate|pick_rate`.
Returns `HeroRanking[]` descending by `sort`:
```json
{"id":88,"name":"Masha","slug":"masha","head_image":"…",
 "win_rate":0.610973,"ban_rate":0.434391,"pick_rate":0.005478,"tier":"S+"}
```

### `GET /heroes/{identifier}`
`identifier` = numeric in-game id, slug, or name (`78`, `khufra`, `Khufra`).
Returns `HeroDetail`:
```json
{"id":78,"name":"Khufra","slug":"khufra","roles":["Tank"],"lanes":["Roam"],
 "specialties":["Initiator","Crowd Control"],"head_image":"…","portrait":"…",
 "skills":[{"name":"Spell Curse","description":"…"}],
 "strong_against":["Joy","Lancelot"],"weak_against":["Fredrinn","Gloo"],
 "rank_stat":{"win_rate":0.546321,"ban_rate":0.020853,"pick_rate":0.003423}}
```

### Player endpoints (consented sign-in)

The app connects **the player's own account**. No password is ever requested:
the player receives a one-time code in their in-game mailbox and exchanges it
for a session. The upstream JWT stays on the backend; the app only receives an
opaque session key, sent back as `Authorization: Bearer <sessionToken>`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/players/connect/start` | `{playerId, zoneId}` → sends the in-game code |
| POST | `/players/connect/verify` | `{playerId, zoneId, code}` → `{sessionToken, player}` |
| POST | `/players/disconnect` | forgets the session (Bearer token) |
| GET | `/players/me/profile` | IGN, avatar, level, rank level |
| GET | `/players/me/stats` | matches, wins, win rate, avg score, MVP count, win streak |
| GET | `/players/me/matches` | recent matches: hero, K/D/A, KDA, MVP flag, win/loss, score, lane, timestamp |
| GET | `/players/me/heroes` | most-played heroes with win rate |
| GET | `/players/{player_id}/{zone_id}` | **501** — anonymous lookup of *other* players is not supported |

```json
// GET /players/me/matches
{"battleId":"...","heroId":88,"heroName":"Masha","kills":8,"deaths":2,"assists":5,
 "kda":6.5,"mvp":true,"won":true,"score":92,"laneId":1,"playedAt":"2026-11-14T10:00:00+00:00"}
```

Field meanings are taken from the provider's own documentation: `res` 1 = win /
0 = loss, `s` = match score out of 100, `lid` = lane, `mvp` = 1/0. `kda` is
derived from the real K/D/A as `(kills + assists) / max(deaths, 1)`.

### `GET /heroes/{identifier}/history`
Recorded daily snapshots — **our own observation history**, not provider data.
A snapshot row is written whenever the backend fetches the 7-day rankings live
(one per hero per UTC day, idempotent). Returns `count: 0` with an explanatory
`meta.note` until the backend has recorded at least one fetch. Empty `sources`
by design: this data comes from this backend's database.
```json
{"capturedOn":"2026-11-14","winRate":0.606971,"banRate":0.048624,
 "pickRate":0.018798,"tier":"S+","rankPosition":1}
```
Populate the table with `backend/scripts/record_snapshot.py` (safe to schedule;
one row per hero per UTC day).

### `GET /esports/{league}/standings`
`league` ∈ `id | ph | my | kh` (MPL Indonesia, Philippines, Malaysia, Cambodia).
```json
{"rank":1,"teamCode":"TLID","teamName":"TEAM LIQUID ID","logo":"https://…",
 "matchPoint":12,"matchWins":12,"matchLosses":4,"netGameWin":15,"gameWins":26,"gameLosses":11}
```

### `GET /players/{player_id}/{zone_id}`
Numeric ids only. Returns **`501 NOT_SUPPORTED`** — looking up *another*
player requires their consent, so only the consented connect flow above
serves player statistics. Body:
```json
{"status":"error","code":"NOT_SUPPORTED",
 "message":"Player statistics require connecting your own account.",
 "details":"Moonton exposes no public endpoint for another player's profile, match history or rank. …"}
```

### Error codes
`NOT_FOUND` (404) · `PROVIDER_AUTH_REQUIRED` (401) · `VALIDATION_ERROR` (422) ·
`NOT_SUPPORTED` (501) · `PROVIDER_ERROR` (502) · `PROVIDER_UNAVAILABLE` (503) ·
`INTERNAL_ERROR` (500).

---

## B. External providers

### Rone Arena — `https://arena.rone.dev/api` (mirror: `https://arena.fastapicloud.dev/api`)
Unofficial, community-maintained; no API key. OpenAPI 3.1, v1.6.2, 65 operations.

| Endpoint | Auth | Used for |
|---|---|---|
| `GET /heroes?size=&index=&lang=` | none | hero ids, portraits, relations |
| `GET /heroes/rank?days=&rank=&sort_field=&sort_order=&size=&lang=` | none | win/ban/pick rankings |
| `GET /heroes/{id}/counters`, `/relations`, `/stats`, `/trends` | none | relationships, stats |
| `GET /academy/{roles,equipment,emblems,spells,ranks,recommended}` | none | academy data |
| `GET /academy/heroes/{id}/{builds?lane=,lane,stats,timeline}` | none | per-hero academy |
| `GET /esports/{league}/{standings,schedule,playoffs,matches/{id}}` | none | MPL ID/PH/MY/KH |
| `POST /user/auth/send-vc` | — | sends the one-time code to the player's in-game mailbox |
| `POST /user/auth/login` | — | exchanges the code for `data.jwt` (bearer token) |
| `POST /user/auth/logout` | JWT | ends the provider session |
| `GET /user/{info,stats,season,matches,heroes/frequent,friends}` | **JWT** | player data — the connected account only |

Notes: `days` ∈ {1,3,7,15,30}; `rank` ∈ {all, epic, legend, mythic, honor, glory};
`size` default 20 (paginate with `index`; `total` = 133 heroes). `builds` requires
`lane`. `/user/*` requires `Authorization: Bearer <jwt>` — verified `401` without
a session, and `200` with one.

**Player field semantics** (from the provider's own docs): `tc` total matches,
`wc` wins, `as` average score (/100), `gt` playtime hours, `mvpc` MVP count,
`wsc` win streak; in match records `k/d/a` kills/deaths/assists, `res`
(1 = win, 0 = loss), `s` score (/100), `lid` lane, `mvp` 1/0, `ts` timestamp,
`pageInfo.nextCursor` for pagination.

> Provider quirk: `/user/auth/login` answers **HTTP 500** (its own
> `ResponseValidationError`) for an invalid code or unknown account, and
> `send-vc` can return `code: 0` even for an unknown id. The backend maps
> these to `401 PROVIDER_AUTH_REQUIRED` with honest copy instead of a raw
> 500.

### MLBBDex — `https://mlbbdex.com/api/v1`
No key, static cached JSON. 134 heroes, 102 items, 276 patches.

| Endpoint | Returns |
|---|---|
| `GET /heroes` | slug, name, roles, lanes, specialties, skills (names) |
| `GET /heroes/{slug}` | stats, skills + descriptions, artwork |
| `GET /rankings` | tier + win/ban/pick, `measuredAt` |
| `GET /patches` | versions |

Terms: credit the source (CC BY-SA). Responses carry attribution; our envelope
preserves it in `meta.sources`.

### Not usable
- `mlbb.rone.dev`, `ronearena.com` — DNS does not resolve.
- `rantey.com` — a game *account generator* site, not an MLBB statistics API.
- `mobilelegends.com` — JS SPA, no documented public JSON API.
