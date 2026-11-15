"""Player service.

Two capabilities:

* ``lookup`` — anonymous lookup by ID/zone. Still unsupported: no public
  source serves another player's stats without their consent.
* **connected mode** — the player signs in as themselves with a one-time code
  delivered in-game. The provider JWT stays on the server; the app receives an
  opaque session key.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.errors import NotSupportedError, ProviderAuthError
from app.core.logging import get_logger
from app.db.models import PlayerSession
from app.db.repo import delete_session, find_session, save_session, touch_session
from app.integrations.models import (
    FrequentHeroData,
    PlayerMatchesPage,
    PlayerProfileData,
    PlayerStatsData,
)
from app.integrations.provider_factory import Providers
from app.schemas.player import PlayerProfile

logger = get_logger(__name__)

_UNSUPPORTED_MESSAGE = "Player statistics require connecting your own account."
_UNSUPPORTED_DETAILS = (
    "Moonton exposes no public endpoint for another player's profile, match history "
    "or rank. MLBB Tracker now supports a consented sign-in: enter your own Player ID "
    "and Zone ID, receive a one-time code in your in-game mailbox, and connect. The "
    "backend then reads your real statistics. Anonymous lookups are not supported and "
    "nothing is ever fabricated."
)


class PlayerService:
    def __init__(
        self,
        providers: Providers,
        *,
        session_factory: Callable[[], Session] | None = None,
    ) -> None:
        self._providers = providers
        self._session_factory = session_factory

    # — Anonymous lookup (unchanged: not permitted) ————————————————
    async def lookup(self, player_id: str, zone_id: str) -> PlayerProfile:
        data = await self._providers.player.fetch_player(player_id, zone_id)
        return PlayerProfile.from_domain(data)

    # — Consented connection ————————————————————————————————————
    def _session_provider(self):
        rone = self._providers.rone
        if rone is None:
            raise NotSupportedError(
                "Player connection is disabled.",
                "Set MLBB_ENABLE_RONE=true to enable the consented player sign-in.",
            )
        return rone

    async def start_connect(self, player_id: str, zone_id: str) -> None:
        await self._session_provider().send_verification_code(player_id, zone_id)

    async def verify_connect(
        self, player_id: str, zone_id: str, code: str
    ) -> tuple[str, PlayerProfileData]:
        if self._session_factory is None:
            raise NotSupportedError(
                "Player connection is unavailable.",
                "The backend has no database configured for player sessions.",
            )
        provider = self._session_provider()
        token = await provider.login(player_id, zone_id, code)
        info = await provider.user_info(token)
        session_key = secrets.token_urlsafe(32)
        save_session(
            self._session_factory,
            session_key=session_key,
            provider_token=token,
            role_id=info.player_id or player_id,
            zone_id=info.zone_id or zone_id,
            ign=info.ign,
        )
        logger.info("player connected: role=%s zone=%s", player_id, zone_id)
        return session_key, info

    async def disconnect(self, session_key: str) -> None:
        row = self._require_session(session_key)
        try:
            await self._session_provider().logout(row.provider_token)
        except Exception:  # noqa: BLE001 — local cleanup must still succeed
            logger.info("provider logout failed; clearing local session anyway")
        delete_session(self._session_factory, session_key)

    async def profile(self, session_key: str) -> PlayerProfileData:
        token = self._token(session_key)
        return await self._session_provider().user_info(token)

    async def stats(self, session_key: str) -> PlayerStatsData:
        token = self._token(session_key)
        return await self._session_provider().user_stats(token)

    async def matches(
        self, session_key: str, *, limit: int = 20, cursor: str | None = None
    ) -> PlayerMatchesPage:
        token = self._token(session_key)
        return await self._session_provider().user_matches(token, limit=limit, cursor=cursor)

    async def frequent_heroes(
        self, session_key: str, *, limit: int = 10
    ) -> list[FrequentHeroData]:
        token = self._token(session_key)
        return await self._session_provider().user_frequent_heroes(token, limit=limit)

    # — Internals ————————————————————————————————————————————————
    def _require_session(self, session_key: str) -> PlayerSession:
        if self._session_factory is None:
            raise ProviderAuthError("No player is connected.")
        row = find_session(self._session_factory, session_key)
        if row is None:
            raise ProviderAuthError("Session not found. Please connect your account again.")
        return row

    def _token(self, session_key: str) -> str:
        row = self._require_session(session_key)
        touch_session(self._session_factory, session_key)
        return row.provider_token
