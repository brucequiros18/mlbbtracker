"""Player data provider.

Milestone 1 finding: no legitimate public source exposes per-player
statistics. Rone Arena's ``/user/*`` endpoints require authenticating *as*
the player (``POST /api/user/auth/send-vc`` + ``/login``), which would mean
handling a player's account credentials — explicitly out of scope and
forbidden by the project rules.

Rather than fabricate data, the default provider reports the capability as
unsupported. If a permitted, consented source is added later, implement
``PlayerProvider`` and register it in the provider factory.
"""

from __future__ import annotations

from app.core.errors import NotSupportedError
from app.integrations.base_provider import PlayerProvider
from app.integrations.models import PlayerProfileData

_UNSUPPORTED_MESSAGE = "Player statistics are not available from any permitted public source."
_UNSUPPORTED_DETAILS = (
    "Moonton exposes no public player rankings, match history or profile endpoint. "
    "The only API that offers player data (Rone Arena /user/*) requires signing in as the "
    "player with a one-time code, which this app does not do. MLBB Tracker therefore shows "
    "verified hero and meta data only, and never displays fabricated player statistics."
)


class NullPlayerProvider(PlayerProvider):
    name = "unavailable"

    async def fetch_player(self, player_id: str, zone_id: str) -> PlayerProfileData:
        raise NotSupportedError(_UNSUPPORTED_MESSAGE, _UNSUPPORTED_DETAILS)


def unsupported_message() -> tuple[str, str]:
    return _UNSUPPORTED_MESSAGE, _UNSUPPORTED_DETAILS
