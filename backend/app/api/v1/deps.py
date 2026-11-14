"""FastAPI dependency providers."""

from __future__ import annotations

from functools import partial

from app.core.config import get_settings
from app.db.base import get_session_factory
from app.db.repo import record_rankings
from app.integrations.provider_factory import get_providers
from app.services.esports_service import EsportsService
from app.services.hero_service import HeroService
from app.services.player_service import PlayerService


def get_hero_service() -> HeroService:
    session_factory = get_session_factory()
    return HeroService(
        get_providers(),
        get_settings(),
        recorder=partial(record_rankings, session_factory),
        session_factory=session_factory,
    )


def get_player_service() -> PlayerService:
    return PlayerService(get_providers())


def get_esports_service() -> EsportsService:
    return EsportsService(get_providers(), get_settings())
