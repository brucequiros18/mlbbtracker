"""Health checks, including optional live provider probes."""

from __future__ import annotations

from app.core.cache import cache
from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.provider_factory import Providers


async def health_payload(settings: Settings, providers: Providers) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "cache": cache.stats(),
        "providers": {
            "hero_identity": providers.rone.name if providers.rone else None,
            "hero_meta": providers.mlbbdex.name if providers.mlbbdex else None,
            "ranking": (providers.rone.name if providers.rone else (providers.mlbbdex.name if providers.mlbbdex else None)),
            "player": providers.player.name,
        },
        "capabilities": {
            "hero_catalog": providers.rone is not None,
            "hero_detail": providers.mlbbdex is not None,
            "hero_rankings": providers.rone is not None or providers.mlbbdex is not None,
            "player_lookup": settings.enable_player_lookup,
        },
    }


async def probe_providers(providers: Providers) -> dict:
    """Issue a lightweight live call to each provider and report reachability."""
    results: dict[str, object] = {}

    if providers.rone is not None:
        try:
            refs = await providers.rone.fetch_hero_refs()
            results["rone_arena"] = {"status": "up", "heroes": len(refs)}
        except AppError as exc:
            results["rone_arena"] = {"status": "down", "error": exc.code}

    if providers.mlbbdex is not None:
        try:
            metas = await providers.mlbbdex.fetch_hero_catalog()
            results["mlbbdex"] = {"status": "up", "heroes": len(metas)}
        except AppError as exc:
            results["mlbbdex"] = {"status": "down", "error": exc.code}

    return results
