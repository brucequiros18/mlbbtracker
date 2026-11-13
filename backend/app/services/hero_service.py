"""Hero service: merges providers into the normalized API shapes.

Responsibilities:
* combine identity (Rone Arena: ids, portraits, relations) with metadata
  (MLBBDex: roles, lanes, skills, tiers);
* cache provider results with type-appropriate TTLs;
* never invent a field — if a provider does not supply something it is left
  empty rather than filled with a placeholder value.
"""

from __future__ import annotations

from app.core.cache import cache
from app.core.config import Settings
from app.core.errors import AppError, NotFoundError
from app.core.logging import get_logger
from app.integrations.models import HeroRef, normalize_hero_name
from app.integrations.provider_factory import Providers
from app.schemas.hero import (
    HeroDetail,
    HeroRankStat,
    HeroRanking,
    HeroSummary,
    detail_from_data,
    summary_from_ref,
)

logger = get_logger(__name__)


class HeroService:
    def __init__(self, providers: Providers, settings: Settings) -> None:
        self._providers = providers
        self._settings = settings

    # — Catalog ————————————————————————————————————————————————
    async def catalog(self, *, role: str | None = None, lane: str | None = None) -> list[HeroSummary]:
        heroes = await self._catalog_raw()
        if role and role.lower() != "all":
            heroes = [h for h in heroes if role.lower() in [r.lower() for r in h.roles]]
        if lane and lane.lower() != "all":
            heroes = [h for h in heroes if lane.lower() in [l.lower() for l in h.lanes]]
        return sorted(heroes, key=lambda h: h.name.lower())

    async def _catalog_raw(self) -> list[HeroSummary]:
        key = "catalog:v1"
        cached = cache.get(key)
        if isinstance(cached, list):
            return cached

        refs: list[HeroRef] = await self._providers.identity().fetch_hero_refs()

        metas = []
        try:
            metas = await self._providers.meta().fetch_hero_catalog()
        except AppError as exc:
            logger.warning("hero metadata unavailable: %s", exc.message)

        meta_by_key = {normalize_hero_name(m.name): m for m in metas}
        tiers = await self._tier_map()

        heroes: list[HeroSummary] = []
        for ref in refs:
            k = normalize_hero_name(ref.name)
            meta = meta_by_key.get(k)
            heroes.append(
                summary_from_ref(
                    ref,
                    slug=meta.slug if meta else k,
                    roles=meta.roles if meta else [],
                    lanes=meta.lanes if meta else [],
                    tier=tiers.get(k),
                )
            )

        cache.set(key, heroes, self._settings.cache_ttl_catalog)
        return heroes

    async def _tier_map(self) -> dict[str, str | None]:
        key = "tiers:v1"
        cached = cache.get(key)
        if isinstance(cached, dict):
            return cached
        tiers: dict[str, str | None] = {}
        dex = self._providers.mlbbdex
        if dex is not None:
            try:
                for entry in await dex.fetch_rankings():
                    if entry.tier:
                        tiers[normalize_hero_name(entry.name)] = entry.tier
            except AppError as exc:
                logger.warning("tier map unavailable: %s", exc.message)
        cache.set(key, tiers, self._settings.cache_ttl_catalog)
        return tiers

    # — Rankings ————————————————————————————————————————————————
    async def rankings(
        self, *, days: int = 7, rank: str = "all", sort_field: str = "win_rate"
    ) -> list[HeroRanking]:
        key = f"rankings:v1:{days}:{rank}:{sort_field}"
        cached = cache.get(key)
        if isinstance(cached, list):
            return cached

        entries = await self._providers.ranking().fetch_rankings(
            days=days, rank=rank, sort_field=sort_field
        )
        catalog = await self._catalog_raw()
        by_name = {normalize_hero_name(h.name): h for h in catalog}
        tiers = await self._tier_map()

        rows: list[HeroRanking] = []
        for entry in entries:
            k = normalize_hero_name(entry.name)
            known = by_name.get(k)
            resolved = entry.__class__(
                id=entry.id if entry.id is not None else (known.id if known else 0),
                name=entry.name,
                slug=entry.slug or (known.slug if known else k),
                head_image=entry.head_image or (known.head_image if known else None),
                win_rate=entry.win_rate,
                ban_rate=entry.ban_rate,
                pick_rate=entry.pick_rate,
                tier=entry.tier or tiers.get(k),
            )
            rows.append(HeroRanking.from_entry(resolved, slug=resolved.slug, tier=resolved.tier))

        rows.sort(key=lambda r: getattr(r, sort_field, r.win_rate), reverse=True)
        cache.set(key, rows, self._settings.cache_ttl_rankings)
        return rows

    # — Detail ————————————————————————————————————————————————
    async def hero(self, identifier: str) -> HeroDetail:
        catalog = await self._catalog_raw()
        match = self._resolve(catalog, identifier)
        if match is None:
            raise NotFoundError(f"No hero matches '{identifier}'.")

        detail = await self._providers.meta().fetch_hero_detail(match.slug)

        refs = await self._identity_refs()
        by_id = {r.id: r for r in refs}
        strong = [by_id[i].name for i in (by_id.get(match.id).strong_ids if by_id.get(match.id) else []) if i in by_id]
        weak = [by_id[i].name for i in (by_id.get(match.id).weak_ids if by_id.get(match.id) else []) if i in by_id]

        rank_stat = await self._rank_stat_for(match.id)

        return detail_from_data(
            detail,
            hero_id=match.id,
            head_image=match.head_image,
            strong_against=strong,
            weak_against=weak,
            rank_stat=rank_stat,
        )

    async def _identity_refs(self) -> list[HeroRef]:
        key = "refs:v1"
        cached = cache.get(key)
        if isinstance(cached, list):
            return cached
        refs = await self._providers.identity().fetch_hero_refs()
        cache.set(key, refs, self._settings.cache_ttl_catalog)
        return refs

    async def _rank_stat_for(self, hero_id: int) -> HeroRankStat | None:
        try:
            rows = await self.rankings(days=7, rank="all", sort_field="win_rate")
        except AppError:
            return None
        for row in rows:
            if row.id == hero_id:
                return HeroRankStat(
                    win_rate=row.win_rate, ban_rate=row.ban_rate, pick_rate=row.pick_rate
                )
        return None

    @staticmethod
    def _resolve(catalog: list[HeroSummary], identifier: str) -> HeroSummary | None:
        if identifier.isdigit():
            target = int(identifier)
            return next((h for h in catalog if h.id == target), None)
        k = normalize_hero_name(identifier)
        return next(
            (h for h in catalog if normalize_hero_name(h.slug) == k or normalize_hero_name(h.name) == k),
            None,
        )
