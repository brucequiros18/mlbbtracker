"""Player API schemas."""

from __future__ import annotations

from dataclasses import asdict

from pydantic import Field

from app.integrations.models import (
    FrequentHeroData,
    PlayerMatchData,
    PlayerProfileData,
    PlayerStatsData,
)
from app.schemas.common import ApiModel


class PlayerProfile(ApiModel):
    player_id: str
    zone_id: str
    ign: str
    avatar: str | None = None
    level: int | None = None
    rank_level: int | None = None
    rank_name: str | None = None
    rank_icon: str | None = None
    total_matches: int | None = None
    wins: int | None = None
    losses: int | None = None
    win_rate: float | None = None
    kda: float | None = None
    mvp_count: int | None = None

    @classmethod
    def from_domain(cls, data: PlayerProfileData) -> "PlayerProfile":
        return cls(**asdict(data))


class PlayerStats(ApiModel):
    """Aggregate stats for the signed-in player (provider field semantics)."""

    total_matches: int | None = None
    wins: int | None = None
    win_rate: float | None = None
    avg_score: float | None = None
    playtime_hours: float | None = None
    mvp_count: int | None = None
    win_streak: int | None = None

    @classmethod
    def from_domain(cls, data: PlayerStatsData) -> "PlayerStats":
        return cls(**asdict(data))


class PlayerMatch(ApiModel):
    battle_id: str | None = None
    season_id: int | None = None
    hero_id: int | None = None
    hero_name: str | None = None
    hero_icon: str | None = None
    kills: int
    deaths: int
    assists: int
    kda: float
    mvp: bool
    won: bool
    score: int | None = None
    lane_id: int | None = None
    played_at: str

    @classmethod
    def from_domain(cls, data: PlayerMatchData) -> "PlayerMatch":
        return cls(**asdict(data))


class PlayerMatchesPage(ApiModel):
    data: list[PlayerMatch]
    next_cursor: str | None = None
    has_next: bool = False


class FrequentHero(ApiModel):
    hero_id: int | None = None
    hero_name: str | None = None
    hero_icon: str | None = None
    total_matches: int | None = None
    wins: int | None = None
    win_rate: float | None = None

    @classmethod
    def from_domain(cls, data: FrequentHeroData) -> "FrequentHero":
        return cls(**asdict(data))


class ConnectRequest(ApiModel):
    """Step 1: identify yourself. Values come from your in-game profile."""

    player_id: str = Field(min_length=1, max_length=32, pattern=r"^\d+$")
    zone_id: str = Field(min_length=1, max_length=16, pattern=r"^\d+$")


class ConnectVerifyRequest(ConnectRequest):
    """Step 2: the one-time code delivered to your in-game mailbox."""

    code: str = Field(min_length=4, max_length=8, pattern=r"^\d+$")


class ConnectStart(ApiModel):
    sent: bool
    message: str


class ConnectVerify(ApiModel):
    session_token: str
    player: PlayerProfile
