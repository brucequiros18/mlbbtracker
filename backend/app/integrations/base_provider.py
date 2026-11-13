"""Abstract provider interfaces.

Two narrow interfaces are used instead of one fat one, so a provider only
implements what it actually offers:

* ``HeroIdentityProvider`` — canonical hero ids/portraits and relationships.
* ``HeroMetaProvider`` — descriptive metadata and per-hero detail.
* ``HeroRankingProvider`` — win/ban/pick rankings.
* ``PlayerProvider`` — per-player profiles.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.integrations.models import (
    HeroDetailData,
    HeroMeta,
    HeroRef,
    PlayerProfileData,
    RankingEntry,
    TrendPoint,
)


class HeroIdentityProvider(ABC):
    name: str = "identity"

    @abstractmethod
    async def fetch_hero_refs(self) -> list[HeroRef]: ...


class HeroMetaProvider(ABC):
    name: str = "meta"

    @abstractmethod
    async def fetch_hero_catalog(self) -> list[HeroMeta]: ...

    @abstractmethod
    async def fetch_hero_detail(self, slug: str) -> HeroDetailData: ...


class HeroRankingProvider(ABC):
    name: str = "ranking"

    @abstractmethod
    async def fetch_rankings(
        self, *, days: int = 7, rank: str = "all", sort_field: str = "win_rate"
    ) -> list[RankingEntry]: ...


class HeroTrendProvider(ABC):
    name: str = "trend"

    @abstractmethod
    async def fetch_trends(self, hero_id: int, *, days: int = 7) -> list[TrendPoint]: ...


class PlayerProvider(ABC):
    name: str = "player"

    @abstractmethod
    async def fetch_player(self, player_id: str, zone_id: str) -> PlayerProfileData: ...
