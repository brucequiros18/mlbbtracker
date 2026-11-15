# Milestone 1 — Research & Architecture

Date of verification: **2026-11-13**. Every endpoint below was called live; raw
responses are stored in [`docs/research/samples/`](research/samples/).

---

## 1. Development environment assessment

| Tool | Version | Status |
|---|---|---|
| OS | Windows 11 (build 26300) | ✅ |
| Flutter | 3.41.3 (stable) | ✅ `flutter doctor`: no issues |
| Dart | 3.11.1 | ✅ |
| Android SDK | 36.1.0 (build-tools, platform-tools, NDK) | ✅ |
| Android emulators | `Medium_Phone_API_36.1`, `Pixel` | ✅ |
| Java (OpenJDK) | 17.0.19 LTS | ✅ required by Gradle |
| Python | 3.13.14 | ✅ (spec suggested 3.12; 3.13 verified working) |
| Node / npm | 26.13.0 / 11.20.0 | ✅ (tooling only) |
| Git | 2.56.0 | ✅ |
| Visual Studio | Community 2026 18.7.0 | ✅ |
| Bruno (API client) | not installed | ℹ️ optional; curl/PowerShell used instead |

Repository `D:\projs\project1` was **empty** — this is a greenfield project.

## 2. API comparison

The brief listed Rone Arena, Rantey, "official Moonton", and other community
projects. Findings:

| Candidate | Verdict | Notes |
|---|---|---|
| **Rone Arena API** (`arena.rone.dev/api`) | ✅ **Use** | 65 operations, OpenAPI 3.1, no key, version 1.6.2. Heroes, academy (builds, equipment, emblems, spells), esports (MPL ID/PH/MY/KH), addons. `user/*` needs player sign-in. |
| **MLBBDex** (`mlbbdex.com/api/v1`) | ✅ **Use** | No key, cached JSON. Heroes, hero detail, rankings (tier), patches. Clean data; explicitly "no player data". |
| `mlbb.rone.dev` (older host) | ❌ Dead | DNS does not resolve. Rone Arena moved hosts; use `arena.rone.dev` (primary alias `arena.fastapicloud.dev`). |
| `ronearena.com` | ❌ Dead | DNS does not resolve. |
| **Rantey API** (`rantey.com`) | ❌ **Not an MLBB API** | It is a mobile-game *account generator* site (Car Parking Multiplayer, PUBG). No MLBB statistics; unusable. |
| Official Moonton (`mobilelegends.com`) | ⚠️ Not directly usable | The hero-stats page is a JS SPA with no documented public JSON API; a Kaggle scraper hits an internal backend. Rone Arena already re-serves this data. |
| `mlbb.gg` (via parse.bot), `api-mobilelegends` (Vercel) | ⚠️ Limited | Hero attributes/synergies only; the Vercel API is a mirror of the same Rone Arena project. |
| Kaggle datasets | ⚠️ Snapshot only | Static CSVs; not a live API. |

## 3. Verified endpoints & sample responses

### Rone Arena — `https://arena.rone.dev/api`

| Endpoint | Auth | Verified | Returns |
|---|---|---|---|
| `GET /heroes?size=&index=&lang=` | none | 200 | hero_id, name, portrait, relations (strong/weak ids) |
| `GET /heroes/rank?days=&rank=&sort_field=&sort_order=&size=&lang=` | none | 200 | win/ban/pick rates + counter ids |
| `GET /heroes/{id}/counters` | none | 200 | counter/relationship rows |
| `GET /academy/heroes/{id}/builds?lane=` | none | 200 | recommended builds (`lane` required) |
| `GET /academy/heroes/{id}/stats` | none | 200 | ranked stats |
| `GET /academy/{equipment,emblems,spells,ranks}` | none | 200 | academy reference data |
| `GET /esports/{id,ph,my,kh}/standings` | none | 200 | pro-league standings |
| `GET /user/stats` | **JWT** | **401** | player stats — **requires signing in as the player** |

Sample (`/heroes?size=2`, abridged):

```json
{"code":0,"message":"OK","data":{"total":133,"records":[
  {"data":{"hero":{"data":{"head":"https://wsrv.nl/?url=…","name":"Hirara"}},
   "hero_id":133,
   "relation":{"strong":{"target_hero_id":[52,121,113,56]},"weak":{"target_hero_id":[3,24]}}}}]}}
```

Sample (`/heroes/rank`, abridged):

```json
{"code":0,"message":"OK","data":{"records":[{"data":{
  "main_hero":{"data":{"head":"…","name":"Masha"}},
  "main_heroid":88,
  "main_hero_win_rate":0.610973,
  "main_hero_ban_rate":0.434391,
  "main_hero_appearance_rate":0.005478}}]}}
```

### MLBBDex — `https://mlbbdex.com/api/v1`

| Endpoint | Auth | Verified | Returns |
|---|---|---|---|
| `GET /heroes` | none | 200 | slug, name, roles, lanes, specialties, skills (names) |
| `GET /heroes/{slug}` | none | 200 | stats, skills with descriptions, artwork |
| `GET /rankings` | none | 200 | tier + win/ban/pick rates |
| `GET /patches` | none | 200 | patch versions |

Sample (`/heroes/khufra`, abridged):

```json
{"data":{"slug":"khufra","name":"Khufra","roles":["Tank"],"lanes":["Roam"],
  "specialties":["Initiator","Crowd Control"],"stats":{"hp1":"2779","movement_spd":"255"},
  "skills":[{"name":"Spell Curse","description":"…"}]}}
```

## 4. Data availability matrix

| Requested capability | Publicly available? | Source / reason |
|---|---|---|
| Hero list / detail (names, roles, lanes, skills) | ✅ Yes | Rone Arena + MLBBDex |
| Hero win / ban / pick rate by rank & window | ✅ Yes | Rone Arena `/heroes/rank` |
| Hero tier, counters, synergies, builds | ✅ Yes | MLBBDex + Rone Arena academy |
| Hero leaderboards | ✅ Yes | Rone Arena rankings |
| Esports standings (MPL ID/PH/MY/KH) | ✅ Yes | Rone Arena esports |
| **Player lookup by Player ID + Zone ID** | ❌ **No** | No public endpoint exists for *other* players |
| **Connected player profile / stats / matches** | ✅ **Yes (consented)** | Rone Arena `user/*` after the player signs in with an in-game code |
| **Player rank / win rate / KDA / MVP** | ✅ **Yes (consented)** | Same — own account only |
| **Match history** | ✅ **Yes (consented)** | `user/matches` (cursor-paginated, own account only) |
| **Ranked player leaderboard** | ❌ **No** | Not exposed by any honest source |

> **Update (2026-11-15).** The Milestone-1 conclusion "player data is blocked"
> has been narrowed, not reversed. The source was never missing — what was
> missing was the *consent* step. Rone Arena's own documented flow
> (`POST /user/auth/send-vc` → code in the player's in-game mailbox →
> `POST /user/auth/login` → `data.jwt`) lets a player connect **their own**
> account with a one-time code and no password. The backend now implements that
> flow (token stored server-side, opaque session key on the device) and serves
> real profile, stats, match history and top-hero data. Looking up *other*
> players is still `501 NOT_SUPPORTED` — no honest source exposes it, and
> nothing is fabricated.

## 5. Limitations & risks

1. **Player data — resolved by consent, not by scraping.** No public source
   serves *another* player's stats, and the project rules forbid handling
   Moonton credentials or bypassing auth. The legitimate path is the
   provider's own consent flow, where the player receives a one-time code in
   their in-game mailbox and signs in as themselves. That is implemented; the
   upstream token is stored server-side only.
2. **Unofficial providers.** Rone Arena and MLBBDex are community projects, not
   Moonton-official. They can change or disappear. Mitigation: the provider
   abstraction lets us swap adapters without touching services or the app.
3. **Rate limits / terms.** Both are free and keyless; API caching (TTL) and
   attribution are implemented to stay respectful. CC BY-SA attribution is carried
   in every response envelope.
4. **Data freshness.** Rone Arena reflects Moonton's public services; MLBBDex syncs
   weekly. Timestamps/`measuredAt` are surfaced where providers supply them.
5. **Host drift.** `mlbb.rone.dev` / `ronearena.com` no longer resolve; the live
   hosts are configurable via `MLBB_RONE_BASE_URL` so a future move needs no code change.

## 6. Recommended implementation strategy

Given the findings, the realistic, honest product is an **MLBB hero & meta
analytics tracker** (the "OP.GG hero page" half of the concept) rather than a
player-profile tracker:

- Build everything the data supports, from real endpoints: heroes, meta rankings,
  hero detail, esports.
- Keep the **player search** experience fully built (UI, validation, recent
  searches, provider abstraction) but wire it to an explicit `NOT_SUPPORTED`
  response, with a clear in-app explanation. This preserves the roadmap: if a
  consented player source is ever added, implement one interface and it lights up.
- Never display fabricated player stats in any mode.

This matches the brief's own guidance: *"When blocked by unavailable MLBB data:
continue implementing independently testable UI components, build the provider
abstraction, use clearly labeled mock data only in development and tests,
document the missing capability, do not pretend the integration works."*

## 7. Architecture

```
Flutter (Dart)                      FastAPI (Python)                 Providers
────────────────                    ────────────────                 ─────────
UI (screens)                        /api/v1/heroes        ┐
  │ Riverpod providers              /api/v1/heroes/rankings ├─ HeroService ─ merge/cache ─┬─ RoneArenaProvider  (ids, portraits, rankings)
  ▼                                 /api/v1/heroes/{id}   │                                 └─ MlbbDexProvider   (roles, lanes, skills, tiers)
Repositories ── Dio ──► backend     /api/v1/players/…     ┘  PlayerService ─ NullPlayerProvider (NOT_SUPPORTED)
  (feature-based)                   /api/v1/health
```

- **Provider abstraction**: narrow interfaces (`HeroIdentityProvider`,
  `HeroMetaProvider`, `HeroRankingProvider`, `PlayerProvider`) + a factory.
- **Normalization**: adapters map raw JSON to provider-neutral dataclasses; heroes
  are joined across providers by a name-normalization key.
- **Caching**: in-process TTL cache (swap for Redis later).
- **Errors**: one typed envelope (`code`, `message`, `details`).

## 8. Milestone 1 completion checklist

- [x] Inspect development environment and repository
- [x] Research Rone Arena, Rantey, official and community providers
- [x] Make real requests and capture sanitized sample responses
- [x] Data availability matrix (what is / is not deliverable)
- [x] Document limitations and risks
- [x] Recommend architecture and implementation strategy
- [x] Create repository structure
- [x] Create documentation set (`DEVELOPMENT_PLAN`, `API_DOCUMENTATION`, `DATABASE_SCHEMA`, `UI_UX_GUIDELINES`, `TESTING_REPORT`, `CHANGELOG`)
- [x] Begin implementation (Milestones 2–3: Flutter app + FastAPI backend, verified)
