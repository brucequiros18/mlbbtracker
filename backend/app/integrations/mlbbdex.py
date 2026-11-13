"""MLBBDex adapter (``https://mlbbdex.com/api/v1``).

No key, no quota, static cached JSON. Source data is the Mobile Legends wiki
under CC BY-SA, with ranked stats re-served from the arena.rone.dev community
API. The response envelope carries the attribution, which we preserve.

Verified endpoints (see docs/API_DOCUMENTATION.md):

* ``GET /heroes`` — slug, name, roles, lanes, specialties.
* ``GET /heroes/{slug}`` — full profile: stats, skills with descriptions.
* ``GET /rankings`` — tier plus win/ban/pick rates.
* ``GET /patches`` — patch list.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import NotFoundError, ProviderError
from app.core.logging import get_logger
from app.integrations.base_provider import HeroMetaProvider, HeroRankingProvider
from app.integrations.http import get_json
from app.integrations.models import (
    HeroDetailData,
    HeroMeta,
    HeroSkillData,
    RankingEntry,
)

logger = get_logger(__name__)


class MlbbDexProvider(HeroMetaProvider, HeroRankingProvider):
    name = "mlbbdex"

    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._base = settings.mlbbdex_base_url.rstrip("/")

    async def fetch_hero_catalog(self) -> list[HeroMeta]:
        payload = await get_json(self._client, f"{self._base}/heroes")
        rows = _rows(payload)
        metas = [
            HeroMeta(
                slug=str(row.get("slug") or ""),
                name=str(row.get("name") or ""),
                roles=list(row.get("roles") or []),
                lanes=list(row.get("lanes") or []),
                specialties=list(row.get("specialties") or []),
            )
            for row in rows
            if row.get("slug") and row.get("name")
        ]
        logger.info("mlbbdex: fetched %d hero metas", len(metas))
        return metas

    async def fetch_hero_detail(self, slug: str) -> HeroDetailData:
        payload = await get_json(self._client, f"{self._base}/heroes/{slug}")
        row = _one(payload)
        if row is None:
            raise NotFoundError(f"Hero '{slug}' was not found.")
        skills = [
            HeroSkillData(
                name=str(skill.get("name") or ""),
                description=str(skill.get("description") or ""),
            )
            for skill in (row.get("skills") or [])
            if isinstance(skill, dict)
        ]
        return HeroDetailData(
            slug=str(row.get("slug") or slug),
            name=str(row.get("name") or slug),
            roles=list(row.get("roles") or []),
            lanes=list(row.get("lanes") or []),
            specialties=list(row.get("specialties") or []),
            skills=skills,
            stats={str(k): str(v) for k, v in (row.get("stats") or {}).items()},
        )

    async def fetch_rankings(
        self, *, days: int = 7, rank: str = "all", sort_field: str = "win_rate"
    ) -> list[RankingEntry]:
        # MLBBDex rankings are a single snapshot; days/rank filters are ignored.
        payload = await get_json(self._client, f"{self._base}/rankings")
        data = payload.get("data") if isinstance(payload, dict) else None
        heroes = (data or {}).get("heroes") or []
        entries: list[RankingEntry] = []
        for row in heroes:
            if not isinstance(row, dict) or not row.get("slug"):
                continue
            entries.append(
                RankingEntry(
                    id=None,
                    name=str(row.get("name") or ""),
                    slug=str(row.get("slug")),
                    win_rate=float(row.get("winRate") or 0.0),
                    ban_rate=float(row.get("banRate") or 0.0),
                    pick_rate=float(row.get("pickRate") or 0.0),
                    tier=row.get("tier"),
                )
            )
        logger.info("mlbbdex: fetched %d ranking rows", len(entries))
        return entries

    async def fetch_patches(self) -> list[dict[str, str]]:
        payload = await get_json(self._client, f"{self._base}/patches")
        rows = _rows(payload)
        return [
            {
                "version": str(row.get("version") or ""),
                "title": str(row.get("title") or ""),
                "link": str(row.get("link") or ""),
            }
            for row in rows
        ]


def _rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ProviderError("MLBBDex returned a non-object payload.")
    data = payload.get("data")
    if not isinstance(data, list):
        raise ProviderError("MLBBDex payload had no 'data' list.")
    return [row for row in data if isinstance(row, dict)]


def _one(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        raise ProviderError("MLBBDex returned a non-object payload.")
    data = payload.get("data")
    return data if isinstance(data, dict) else None
