"""Esports API schemas."""

from __future__ import annotations

from app.integrations.models import EsportsStanding
from app.schemas.common import ApiModel


class EsportsStandingRow(ApiModel):
    rank: int
    team_code: str
    team_name: str
    logo: str | None = None
    match_point: int
    match_wins: int
    match_losses: int
    net_game_win: int
    game_wins: int
    game_losses: int

    @classmethod
    def from_domain(cls, row: EsportsStanding) -> "EsportsStandingRow":
        return cls(
            rank=row.rank,
            team_code=row.team_code,
            team_name=row.team_name,
            logo=row.logo,
            match_point=row.match_point,
            match_wins=row.match_wins,
            match_losses=row.match_losses,
            net_game_win=row.net_game_win,
            game_wins=row.game_wins,
            game_losses=row.game_losses,
        )
