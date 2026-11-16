"""Hero service: merges providers into the normalized API shapes.

Responsibilities:
* combine identity (Rone Arena: ids, portraits, relations) with metadata
  (MLBBDex: roles, lanes, skills, tiers);
* cache provider results with type-appropriate TTLs;
* never invent a field — if a provider does not supply something it is left
  empty rather than filled with a placeholder value.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.config import Settings
from app.core.errors import AppError, NotFoundError
from app.core.logging import get_logger
from app.db.models import HeroSnapshot
from app.db.repo import cache_read, cache_write
from app.integrations.models import HeroRef, TrendPoint, normalize_hero_name
from app.integrations.provider_factory import Providers
from app.schemas.hero import (
    HeroDetail,
    HeroHistoryPoint,
    HeroRankStat,
    HeroRanking,
    HeroSummary,
    detail_from_data,
    summary_from_ref,
)

logger = get_logger(__name__)


class HeroService:
    """Hero data service with optional snapshot persistence.

    ``recorder`` (when provided) is called with the raw ranking entries after
    every *fresh* provider fetch, storing daily snapshots. ``session_factory``
    powers the history read path. Both are optional so unit tests can run
    without a database.
    """

    def __init__(
        self,
        providers: Providers,
        settings: Settings,
        *,
        recorder: Callable[[list], int] | None = None,
        session_factory: Callable[[], Session] | None = None,
    ) -> None:
        self._providers = providers
        self._settings = settings
        self._recorder = recorder
        self._session_factory = session_factory

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

        # Cold tier: a restart should not re-fetch the whole catalog upstream.
        stored = self._cache_read(key)
        if stored is not None:
            heroes = [HeroSummary(**row) for row in stored]
            cache.set(key, heroes, self._settings.cache_ttl_catalog)
            logger.info("catalog: served from database cache")
            return heroes

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
        self._cache_write(key, heroes)
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

        stored = self._cache_read(key)
        if stored is not None:
            rows = [HeroRanking(**row) for row in stored]
            cache.set(key, rows, self._settings.cache_ttl_rankings)
            logger.info("rankings: served from database cache")
            return rows

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
        self._cache_write(key, rows)

        # Persist a daily snapshot of the raw provider entries (7-day window
        # only — the canonical analytics window). Failures never break the API.
        if self._recorder is not None and days == 7:
            try:
                recorded = self._recorder(entries)
                if recorded:
                    logger.info("snapshots: recorded %d hero rows", recorded)
            except Exception:  # noqa: BLE001 — persistence must not take the API down
                logger.exception("snapshots: recording failed")

        return rows

    # — Recorded history (from our own database) ————————————————————
    async def history(self, identifier: str, *, days: int = 7) -> list[HeroSnapshot]:
        if self._session_factory is None:
            return []
        catalog = await self._catalog_raw()
        match = self._resolve(catalog, identifier)
        if match is None:
            raise NotFoundError(f"No hero matches '{identifier}'.")
        from app.db.repo import history_for_hero

        return history_for_hero(self._session_factory, match.id, days=days)

    # — Trend timeline ——————————————————————————————————————————
    async def trends(self, identifier: str, *, days: int = 7) -> list[TrendPoint]:
        catalog = await self._catalog_raw()
        match = self._resolve(catalog, identifier)
        if match is None:
            raise NotFoundError(f"No hero matches '{identifier}'.")
        rone = self._providers.rone
        if rone is None:
            return []
        key = f"trends:v1:{match.id}:{days}"
        cached = cache.get(key)
        if isinstance(cached, list):
            return cached
        points = await rone.fetch_trends(match.id, days=days)
        cache.set(key, points, self._settings.cache_ttl_rankings)
        return points

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

    # — Internals ————————————————————————————————————————————————
    def _cache_read(self, key: str) -> list[dict] | None:
        """Read a payload from the database cache tier (cold storage)."""
        if self._session_factory is None:
            return None
        try:
            payload = cache_read(self._session_factory, key)
        except Exception:  # noqa: BLE001 — cache problems must not break the API
            logger.exception("cache read failed for %s", key)
            return None
        if isinstance(payload, list) and all(isinstance(row, dict) for row in payload):
            return payload
        return None

    def _cache_write(self, key: str, rows: list) -> None:
        """Persist normalized rows to the database cache tier."""
        if self._session_factory is None:
            return
        try:
            cache_write(
                self._session_factory,
                key,
                "rone_arena+mlbbdex",
                [row.model_dump() for row in rows],
                self._settings.cache_ttl_rankings
                if key.startswith("rankings")
                else self._settings.cache_ttl_catalog,
            )
        except Exception:  # noqa: BLE001
            logger.exception("cache write failed for %s", key)

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
