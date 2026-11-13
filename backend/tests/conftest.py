"""Shared test fixtures.

Automated tests never touch the network: fake providers stand in for the real
adapters, and adapter parsing is verified separately with an httpx
``MockTransport``.
"""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1.deps import get_hero_service, get_player_service
from app.core.cache import cache
from app.core.config import get_settings
from app.integrations.models import (
    HeroDetailData,
    HeroMeta,
    HeroRef,
    HeroSkillData,
    RankingEntry,
)
from app.integrations.player_provider import NullPlayerProvider
from app.integrations.provider_factory import Providers
from app.main import create_app
from app.services.hero_service import HeroService
from app.services.player_service import PlayerService


class FakeRone:
    name = "fake_rone"

    def __init__(self) -> None:
        self.refs = [
            HeroRef(id=78, name="Khufra", head_image="https://img/khufra.png", strong_ids=[24], weak_ids=[87]),
            HeroRef(id=88, name="Masha", head_image="https://img/masha.png", strong_ids=[], weak_ids=[]),
            HeroRef(id=24, name="Balmond", head_image=None),
            HeroRef(id=87, name="Ruby", head_image=None),
        ]
        self.rankings = [
            RankingEntry(id=88, name="Masha", head_image="https://img/masha.png", win_rate=0.61, ban_rate=0.43, pick_rate=0.0055),
            RankingEntry(id=78, name="Khufra", head_image="https://img/khufra.png", win_rate=0.5463, ban_rate=0.0208, pick_rate=0.0034),
        ]

    async def fetch_hero_refs(self) -> list[HeroRef]:
        return self.refs

    async def fetch_rankings(self, *, days: int = 7, rank: str = "all", sort_field: str = "win_rate"):
        return self.rankings


class FakeDex:
    name = "fake_dex"

    async def fetch_hero_catalog(self) -> list[HeroMeta]:
        return [
            HeroMeta(slug="khufra", name="Khufra", roles=["Tank"], lanes=["Roam"]),
            HeroMeta(slug="masha", name="Masha", roles=["Fighter"], lanes=["Exp"]),
        ]

    async def fetch_hero_detail(self, slug: str) -> HeroDetailData:
        return HeroDetailData(
            slug=slug,
            name=slug.capitalize(),
            roles=["Tank"],
            lanes=["Roam"],
            specialties=["Initiator"],
            skills=[HeroSkillData(name="Spell Curse", description="Enhances the next basic attack.")],
            stats={"hp1": "2779"},
        )

    async def fetch_rankings(self, *, days: int = 7, rank: str = "all", sort_field: str = "win_rate"):
        return [
            RankingEntry(id=None, name="Khufra", slug="khufra", tier="A+"),
            RankingEntry(id=None, name="Masha", slug="masha", tier="S+"),
        ]


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def fake_providers() -> Providers:
    return Providers(
        client=httpx.AsyncClient(),
        rone=FakeRone(),  # type: ignore[arg-type]
        mlbbdex=FakeDex(),  # type: ignore[arg-type]
        player=NullPlayerProvider(),
    )


@pytest.fixture
def client(fake_providers: Providers) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_hero_service] = lambda: HeroService(fake_providers, get_settings())
    app.dependency_overrides[get_player_service] = lambda: PlayerService(fake_providers)
    with TestClient(app) as c:
        yield c
