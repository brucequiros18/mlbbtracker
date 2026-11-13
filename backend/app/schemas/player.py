"""Player API schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.integrations.models import PlayerProfileData


class PlayerProfile(BaseModel):
    player_id: str
    zone_id: str
    ign: str
    avatar: str | None = None
    level: int | None = None
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
        return cls(**data.__dict__)
