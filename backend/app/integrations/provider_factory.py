"""Builds and wires provider adapters from configuration.

Adding or swapping a provider means implementing an interface and updating
this factory — no service or endpoint code changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import httpx

from app.core.config import Settings, get_settings
from app.core.errors import ProviderUnavailableError
from app.integrations.base_provider import (
    HeroIdentityProvider,
    HeroMetaProvider,
    HeroRankingProvider,
    PlayerProvider,
)
from app.integrations.http import build_client
from app.integrations.mlbbdex import MlbbDexProvider
from app.integrations.player_provider import NullPlayerProvider
from app.integrations.rone_arena import RoneArenaProvider


@dataclass
class Providers:
    client: httpx.AsyncClient
    rone: RoneArenaProvider | None
    mlbbdex: MlbbDexProvider | None
    player: PlayerProvider

    async def aclose(self) -> None:
        await self.client.aclose()

    def identity(self) -> HeroIdentityProvider:
        if self.rone is None:
            raise ProviderUnavailableError(
                "No hero identity provider is enabled (set MLBB_ENABLE_RONE=true)."
            )
        return self.rone

    def meta(self) -> HeroMetaProvider:
        if self.mlbbdex is None:
            raise ProviderUnavailableError(
                "No hero metadata provider is enabled (set MLBB_ENABLE_MLBBDEX=true)."
            )
        return self.mlbbdex

    def ranking(self) -> HeroRankingProvider:
        # Rone Arena rankings carry real hero ids and support day/rank windows,
        # so they are preferred; MLBBDex is the fallback.
        if self.rone is not None:
            return self.rone
        if self.mlbbdex is not None:
            return self.mlbbdex
        raise ProviderUnavailableError("No hero ranking provider is enabled.")


@lru_cache
def get_providers() -> Providers:
    settings: Settings = get_settings()
    client = build_client(settings)
    rone = RoneArenaProvider(client, settings) if settings.enable_rone else None
    mlbbdex = MlbbDexProvider(client, settings) if settings.enable_mlbbdex else None
    player: PlayerProvider = NullPlayerProvider()
    return Providers(client=client, rone=rone, mlbbdex=mlbbdex, player=player)
