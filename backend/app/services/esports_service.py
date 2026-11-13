"""Esports service: pro-league standings from the esports provider."""

from __future__ import annotations

from app.core.cache import cache
from app.core.config import Settings
from app.core.errors import ProviderUnavailableError
from app.core.logging import get_logger
from app.integrations.models import EsportsStanding
from app.integrations.provider_factory import Providers

logger = get_logger(__name__)


class EsportsService:
    def __init__(self, providers: Providers, settings: Settings) -> None:
        self._providers = providers
        self._settings = settings

    async def standings(self, league: str) -> list[EsportsStanding]:
        if self._providers.rone is None:
            raise ProviderUnavailableError(
                "No esports provider is enabled (set MLBB_ENABLE_RONE=true)."
            )
        key = f"esports:v1:{league}"
        cached = cache.get(key)
        if isinstance(cached, list):
            return cached
        rows = await self._providers.rone.fetch_standings(league)
        cache.set(key, rows, self._settings.cache_ttl_rankings)
        return rows
