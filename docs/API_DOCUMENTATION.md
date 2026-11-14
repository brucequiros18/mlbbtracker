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
Numeric ids only. Returns **`501 NOT_SUPPORTED`** — no permitted public source
exposes player statistics. Body:
```json
{"status":"error","code":"NOT_SUPPORTED",
 "message":"Player statistics are not available from any permitted public source.",
 "details":"Moonton exposes no public player rankings, match history or profile endpoint. …"}
```

### Error codes
`NOT_FOUND` (404) · `VALIDATION_ERROR` (422) · `NOT_SUPPORTED` (501) ·
`PROVIDER_ERROR` (502) · `PROVIDER_UNAVAILABLE` (503) · `INTERNAL_ERROR` (500).

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
| `POST /user/auth/send-vc`, `/login`, `/logout` | — | **player sign-in (not used)** |
| `GET /user/{info,stats,season,matches,heroes/frequent,friends}` | **JWT** | **player data — 401 without auth** |

Notes: `days` ∈ {1,3,7,15,30}; `rank` ∈ {all, epic, legend, mythic, honor, glory};
`size` default 20 (paginate with `index`; `total` = 133 heroes). `builds` requires
`lane`. `/user/*` requires `Authorization: Bearer <jwt>` — verified `401`.

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
