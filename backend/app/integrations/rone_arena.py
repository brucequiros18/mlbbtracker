"""Rone Arena adapter (``https://arena.rone.dev/api``).

Unofficial, community-maintained API that re-serves Moonton's public game
services. It is the source of canonical hero ids, portraits and hero
win/ban/pick rankings. It requires no API key for public endpoints.

Verified endpoints (see docs/API_DOCUMENTATION.md):

* ``GET /heroes?size=&index=`` — hero ids, names, portraits, relations.
* ``GET /heroes/rank?days=&rank=&sort_field=&size=`` — hero rankings.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.integrations.base_provider import (
    EsportsStandingsProvider,
    HeroIdentityProvider,
    HeroRankingProvider,
    HeroTrendProvider,
)
from app.integrations.http import get_json
from app.integrations.models import EsportsStanding, HeroRef, RankingEntry, TrendPoint

logger = get_logger(__name__)

_PAGE_SIZE = 50
_MAX_PAGES = 8


class RoneArenaProvider(
    HeroIdentityProvider, HeroRankingProvider, HeroTrendProvider, EsportsStandingsProvider
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
