"""Shared test fixtures.

Automated tests never touch the network: fake providers stand in for the real
adapters, and adapter parsing is verified separately with an httpx
``MockTransport``.
"""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1.deps import get_esports_service, get_hero_service, get_player_service
from app.core.cache import cache
from app.core.config import get_settings
from app.integrations.models import (
    EsportsStanding,
    FrequentHeroData,
    HeroDetailData,
    HeroMeta,
    HeroRef,
    HeroSkillData,
    PlayerMatchData,
    PlayerMatchesPage,
    PlayerProfileData,
    PlayerStatsData,
    RankingEntry,
    TrendPoint,
)
from app.integrations.player_provider import NullPlayerProvider
from app.integrations.provider_factory import Providers
from app.main import create_app
from app.services.esports_service import EsportsService
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

    async def fetch_trends(self, hero_id: int, *, days: int = 7) -> list[TrendPoint]:
        return [
            TrendPoint(date="2026-11-10", win_rate=0.548, ban_rate=0.021, pick_rate=0.0034),
            TrendPoint(date="2026-11-11", win_rate=0.550, ban_rate=0.020, pick_rate=0.0035),
        ]

    async def fetch_standings(self, league: str) -> list[EsportsStanding]:
        return [
            EsportsStanding(
                rank=1, team_code="TLPH", team_name=None or "TLPH", logo="logo.png",
                match_point=12, match_wins=12, match_losses=2, net_game_win=19,
                game_wins=25, game_losses=6,
            ),
            EsportsStanding(
                rank=2, team_code="FNOP", team_name="Falcons AP Bren", logo=None,
                match_point=10, match_wins=10, match_losses=4, net_game_win=12,
                game_wins=22, game_losses=10,
            ),
        ]

    # — Player session (consented sign-in) ————————————————————
    async def send_verification_code(self, role_id: str, zone_id: str) -> None:
        if role_id != "123456789":
            from app.core.errors import ProviderAuthError

            raise ProviderAuthError("No such player.")

    async def login(self, role_id: str, zone_id: str, code: str) -> str:
        from app.core.errors import ProviderAuthError

        if code != "111111":
            raise ProviderAuthError("Invalid verification code.")
        return "fake-provider-jwt"

    async def logout(self, token: str) -> None:
        return None

    async def user_info(self, token: str) -> PlayerProfileData:
        return PlayerProfileData(
            player_id="123456789", zone_id="1234", ign="TestPlayer",
            avatar="https://img/avatar.png", level=42, rank_level=7,
        )

    async def user_stats(self, token: str) -> PlayerStatsData:
        return PlayerStatsData(
            total_matches=100, wins=60, win_rate=0.6, avg_score=8.4,
            playtime_hours=52.5, mvp_count=14, win_streak=7,
        )

    async def user_matches(
        self, token: str, *, limit: int = 20, cursor: str | None = None
    ) -> PlayerMatchesPage:
        return PlayerMatchesPage(
            matches=[
                PlayerMatchData(
                    battle_id="9001", season_id=40, hero_id=88, hero_name="Masha",
                    hero_icon="https://img/masha.png", kills=8, deaths=2, assists=5,
                    kda=6.5, mvp=True, won=True, score=92, lane_id=1,
                    played_at="2026-11-13T10:00:00+00:00",
                ),
                PlayerMatchData(
                    battle_id="9000", season_id=40, hero_id=78, hero_name="Khufra",
                    hero_icon="https://img/khufra.png", kills=1, deaths=6, assists=9,
                    kda=1.67, mvp=False, won=False, score=41, lane_id=3,
                    played_at="2026-11-12T09:00:00+00:00",
                ),
            ],
            next_cursor="cursor-2",
            has_next=True,
        )

    async def user_frequent_heroes(
        self, token: str, *, limit: int = 10
    ) -> list[FrequentHeroData]:
        return [
            FrequentHeroData(
                hero_id=88, hero_name="Masha", hero_icon="https://img/masha.png",
                total_matches=40, wins=26, win_rate=0.65,
            )
        ]


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
    app.dependency_overrides[get_esports_service] = lambda: EsportsService(fake_providers, get_settings())
    with TestClient(app) as c:
        yield c
