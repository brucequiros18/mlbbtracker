"""Player service. Delegates to the configured player provider, which by
default reports the capability as unsupported."""

from __future__ import annotations

from app.integrations.provider_factory import Providers
from app.schemas.player import PlayerProfile


class PlayerService:
    def __init__(self, providers: Providers) -> None:
        self._providers = providers

    async def lookup(self, player_id: str, zone_id: str) -> PlayerProfile:
        data = await self._providers.player.fetch_player(player_id, zone_id)
        return PlayerProfile.from_domain(data)
