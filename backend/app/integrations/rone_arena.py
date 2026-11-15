"""Rone Arena adapter (``https://arena.rone.dev/api``).

Unofficial, community-maintained API that re-serves Moonton's public game
services. It is the source of canonical hero ids, portraits and hero
win/ban/pick rankings. It requires no API key for public endpoints.

Verified endpoints (see docs/API_DOCUMENTATION.md):

* ``GET /heroes?size=&index=`` — hero ids, names, portraits, relations.
* ``GET /heroes/rank?days=&rank=&sort_field=&size=`` — hero rankings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ProviderAuthError, ProviderError, ProviderUnavailableError
from app.core.logging import get_logger
from app.integrations.base_provider import (
    EsportsStandingsProvider,
    HeroIdentityProvider,
    HeroRankingProvider,
    HeroTrendProvider,
    PlayerSessionProvider,
)
from app.integrations.http import get_json, post_json
from app.integrations.models import (
    EsportsStanding,
    FrequentHeroData,
    HeroRef,
    PlayerMatchData,
    PlayerMatchesPage,
    PlayerProfileData,
    PlayerStatsData,
    RankingEntry,
    TrendPoint,
)

logger = get_logger(__name__)

_PAGE_SIZE = 50
_MAX_PAGES = 8


class RoneArenaProvider(
    HeroIdentityProvider,
    HeroRankingProvider,
    HeroTrendProvider,
    EsportsStandingsProvider,
    PlayerSessionProvider,
):
    name = "rone_arena"

    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._base = settings.rone_base_url.rstrip("/")

    # — Hero identity ——————————————————————————————————————————
    async def fetch_hero_refs(self) -> list[HeroRef]:
        refs: list[HeroRef] = []
        total: int | None = None
        for index in range(1, _MAX_PAGES + 1):
            payload = await get_json(
                self._client,
                f"{self._base}/heroes",
                params={"size": _PAGE_SIZE, "index": index, "lang": "en"},
            )
            data = _data(payload)
            if data is None:
                raise ProviderError("Rone Arena 'heroes' payload was malformed.")
            records = data.get("records") or []
            if total is None and isinstance(data.get("total"), int):
                total = data["total"]
            if not records:
                break
            for record in records:
                ref = _parse_ref(record)
                if ref is not None:
                    refs.append(ref)
            if total is not None and len(refs) >= total:
                break
        if not refs:
            raise ProviderError("Rone Arena returned no heroes.")
        logger.info("rone: fetched %d hero refs", len(refs))
        return refs

    # — Rankings ————————————————————————————————————————————————
    async def fetch_rankings(
        self, *, days: int = 7, rank: str = "all", sort_field: str = "win_rate"
    ) -> list[RankingEntry]:
        payload = await get_json(
            self._client,
            f"{self._base}/heroes/rank",
            params={
                "days": days,
                "rank": rank,
                "sort_field": sort_field,
                "sort_order": "desc",
                "size": 200,
                "lang": "en",
            },
        )
        data = _data(payload)
        if data is None:
            raise ProviderError("Rone Arena 'heroes/rank' payload was malformed.")
        entries: list[RankingEntry] = []
        for record in data.get("records") or []:
            inner = (record or {}).get("data") or {}
            hero = ((inner.get("main_hero") or {}).get("data")) or {}
            hero_id = inner.get("main_heroid")
            name = hero.get("name")
            if hero_id is None or not name:
                continue
            entries.append(
                RankingEntry(
                    id=int(hero_id),
                    name=str(name),
                    head_image=hero.get("head"),
                    win_rate=float(inner.get("main_hero_win_rate") or 0.0),
                    ban_rate=float(inner.get("main_hero_ban_rate") or 0.0),
                    pick_rate=float(inner.get("main_hero_appearance_rate") or 0.0),
                )
            )
        logger.info("rone: fetched %d ranking rows (days=%s rank=%s)", len(entries), days, rank)
        return entries

    # — Per-hero trend timeline —————————————————————————————————
    async def fetch_trends(self, hero_id: int, *, days: int = 7) -> list[TrendPoint]:
        payload = await get_json(
            self._client,
            f"{self._base}/heroes/{hero_id}/trends",
            params={"rank": "all", "past-days": days, "size": 1, "lang": "en"},
        )
        data = _data(payload)
        if data is None:
            raise ProviderError("Rone Arena 'hero trends' payload was malformed.")
        records = data.get("records") or []
        if not records:
            return []
        points = (((records[0] or {}).get("data") or {}).get("win_rate")) or []
        out = [
            TrendPoint(
                date=str(p.get("date") or ""),
                win_rate=float(p.get("win_rate") or 0.0),
                ban_rate=float(p.get("ban_rate") or 0.0),
                pick_rate=float(p.get("app_rate") or 0.0),
            )
            for p in points
            if isinstance(p, dict) and p.get("date")
        ]
        out.sort(key=lambda p: p.date)  # provider returns newest-first
        logger.info("rone: fetched %d trend points for hero %s", len(out), hero_id)
        return out

    # — Esports standings ———————————————————————————————————————
    async def fetch_standings(self, league: str) -> list[EsportsStanding]:
        # This endpoint returns a bare {"standings": [...]} object rather than
        # the {"code": 0, "data": {...}} envelope used by the game-data routes.
        payload = await get_json(self._client, f"{self._base}/esports/{league}/standings")
        rows = payload.get("standings") if isinstance(payload, dict) else None
        if rows is None:
            raise ProviderError("Rone Arena 'esports standings' payload was malformed.")

        out: list[EsportsStanding] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            team = row.get("team") or {}
            match_wl = row.get("match_wl") or {}
            game_wl = row.get("game_wl") or {}
            code = str(team.get("name") or "")
            out.append(
                EsportsStanding(
                    rank=int(row.get("rank") or 0),
                    team_code=code,
                    # `full_name` is null for some leagues (e.g. MPL PH).
                    team_name=str(team.get("full_name") or code),
                    logo=team.get("logo"),
                    match_point=int(row.get("match_point") or 0),
                    match_wins=int(match_wl.get("win") or 0),
                    match_losses=int(match_wl.get("lose") or 0),
                    net_game_win=int(row.get("net_game_win") or 0),
                    game_wins=int(game_wl.get("win") or 0),
                    game_losses=int(game_wl.get("lose") or 0),
                )
            )
        logger.info("rone: fetched %d standings rows for %s", len(out), league)
        return out


    # — Player session (consented self-login) ————————————————————
    # Contract verified from the provider's own web client and docs:
    # login returns {"code": 0, "data": {"jwt": "<bearer token>"}}; the token is
    # sent as `Authorization: Bearer <jwt>`. The verification code is delivered
    # to the player's own in-game mailbox. No password is involved.

    async def send_verification_code(self, role_id: str, zone_id: str) -> None:
        try:
            payload = await post_json(
                self._client,
                f"{self._base}/user/auth/send-vc",
                json={"role_id": int(role_id), "zone_id": int(zone_id)},
            )
        except ProviderUnavailableError as exc:
            # The provider answers 500 (its own response-validation bug) when the
            # upstream rejects the request; surface it as an auth problem.
            raise ProviderAuthError(
                "The provider could not send a verification code. Check the Player ID "
                "and Zone ID."
            ) from exc
        code = payload.get("code") if isinstance(payload, dict) else None
        if code != 0:
            raise ProviderAuthError(
                _auth_message(payload, "The provider could not send a verification code.")
            )
        logger.info("rone: verification code requested for %s/%s", role_id, zone_id)

    async def login(self, role_id: str, zone_id: str, code: str) -> str:
        try:
            payload = await post_json(
                self._client,
                f"{self._base}/user/auth/login",
                json={"role_id": int(role_id), "zone_id": int(zone_id), "vc": int(code)},
            )
        except ProviderUnavailableError as exc:
            # Same upstream validation failure as above: an invalid code or
            # account produces a 500 rather than a 401.
            raise ProviderAuthError(
                "Sign-in failed. Check the verification code and try again."
            ) from exc
        data = payload.get("data") if isinstance(payload, dict) else None
        token = data.get("jwt") if isinstance(data, dict) else None
        if (payload.get("code") if isinstance(payload, dict) else None) != 0 or not token:
            raise ProviderAuthError(
                _auth_message(payload, "Sign-in failed. Check the code and try again.")
            )
        logger.info("rone: player %s/%s signed in", role_id, zone_id)
        return str(token)

    async def logout(self, token: str) -> None:
        try:
            await post_json(self._client, f"{self._base}/user/auth/logout", bearer=token)
        except Exception:  # noqa: BLE001 — best-effort; the local session is cleared anyway
            logger.info("rone: provider logout failed (ignored)")

    async def user_info(self, token: str) -> PlayerProfileData:
        payload = await get_json(
            self._client, f"{self._base}/user/info", params={"lang": "en"}, bearer=token
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ProviderError("Rone Arena 'user info' payload was malformed.")
        return PlayerProfileData(
            player_id=str(data.get("roleId") or ""),
            zone_id=str(data.get("zoneId") or ""),
            ign=str(data.get("name") or "Unknown"),
            avatar=data.get("avatar"),
            level=data.get("level"),
            rank_level=data.get("rank_level"),
        )

    async def user_stats(self, token: str) -> PlayerStatsData:
        payload = await get_json(
            self._client, f"{self._base}/user/stats", params={"lang": "en"}, bearer=token
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ProviderError("Rone Arena 'user stats' payload was malformed.")
        total = data.get("tc")
        wins = data.get("wc")
        return PlayerStatsData(
            total_matches=total,
            wins=wins,
            win_rate=(wins / total) if isinstance(total, int) and total > 0 and isinstance(wins, int) else None,
            avg_score=data.get("as"),
            playtime_hours=data.get("gt"),
            mvp_count=data.get("mvpc"),
            win_streak=data.get("wsc"),
        )

    async def user_matches(
        self, token: str, *, limit: int = 20, cursor: str | None = None
    ) -> PlayerMatchesPage:
        params: dict[str, Any] = {"limit": limit, "lang": "en"}
        if cursor:
            params["last_cursor"] = cursor
        payload = await get_json(
            self._client, f"{self._base}/user/matches", params=params, bearer=token
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ProviderError("Rone Arena 'user matches' payload was malformed.")
        page_info = data.get("pageInfo") or {}
        rows = data.get("result") or []
        matches = [_parse_match(row) for row in rows]
        next_cursor = page_info.get("nextCursor")
        return PlayerMatchesPage(
            matches=[m for m in matches if m is not None],
            next_cursor=str(next_cursor) if next_cursor not in (None, "") else None,
            has_next=bool(page_info.get("hasNext")),
        )

    async def user_frequent_heroes(
        self, token: str, *, limit: int = 10
    ) -> list[FrequentHeroData]:
        payload = await get_json(
            self._client,
            f"{self._base}/user/heroes/frequent",
            params={"limit": limit, "lang": "en"},
            bearer=token,
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ProviderError("Rone Arena 'frequent heroes' payload was malformed.")
        out: list[FrequentHeroData] = []
        for row in data.get("result") or []:
            if not isinstance(row, dict):
                continue
            hero = row.get("hid_e") or {}
            total = row.get("tc")
            wins = row.get("wc")
            out.append(
                FrequentHeroData(
                    hero_id=row.get("hid"),
                    hero_name=hero.get("n"),
                    hero_icon=hero.get("ix"),
                    total_matches=total,
                    wins=wins,
                    win_rate=(wins / total)
                    if isinstance(total, int) and total > 0 and isinstance(wins, int)
                    else None,
                )
            )
        return out


def _auth_message(payload: Any, fallback: str) -> str:
    if isinstance(payload, dict):
        for key in ("message", "msg"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return fallback


def _parse_match(row: Any) -> PlayerMatchData | None:
    if not isinstance(row, dict):
        return None
    hero = row.get("hid_e") or {}
    kills = int(row.get("k") or 0)
    deaths = int(row.get("d") or 0)
    assists = int(row.get("a") or 0)
    ts = row.get("ts")
    played_at = ""
    if isinstance(ts, (int, float)) and ts > 0:
        seconds = ts / 1000 if ts > 1_000_000_000_000 else ts
        played_at = datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    battle = row.get("bid_s") or row.get("bid")
    return PlayerMatchData(
        battle_id=str(battle) if battle is not None else None,
        season_id=row.get("sid"),
        hero_id=row.get("hid"),
        hero_name=hero.get("n"),
        hero_icon=hero.get("ix"),
        kills=kills,
        deaths=deaths,
        assists=assists,
        kda=round((kills + assists) / max(deaths, 1), 2),
        mvp=row.get("mvp") == 1,
        won=row.get("res") == 1,  # provider docs: 1 = win, 0 = loss
        score=row.get("s"),
        lane_id=row.get("lid"),
        played_at=played_at,
    )


def _data(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    return data if isinstance(data, dict) else None


def _parse_ref(record: Any) -> HeroRef | None:
    if not isinstance(record, dict):
        return None
    inner = record.get("data") or {}
    hero = ((inner.get("hero") or {}).get("data")) or {}
    hero_id = inner.get("hero_id")
    name = hero.get("name")
    if hero_id is None or not name:
        return None
    relation = inner.get("relation") or {}
    strong = ((relation.get("strong") or {}).get("target_hero_id")) or []
    weak = ((relation.get("weak") or {}).get("target_hero_id")) or []
    return HeroRef(
        id=int(hero_id),
        name=str(name),
        head_image=hero.get("head"),
        strong_ids=[int(x) for x in strong if isinstance(x, int)],
        weak_ids=[int(x) for x in weak if isinstance(x, int)],
    )
