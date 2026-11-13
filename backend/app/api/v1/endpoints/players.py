"""Player endpoints.

Returns 501 NOT_SUPPORTED while no permitted player-data source is enabled.
This is intentional and documented — the app must not display fabricated
player statistics.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.deps import get_player_service
from app.schemas.common import ItemResponse, Meta
from app.schemas.player import PlayerProfile
from app.services.player_service import PlayerService

router = APIRouter(prefix="/players", tags=["players"])


@router.get(
    "/{player_id}/{zone_id}",
    response_model=ItemResponse[PlayerProfile],
    summary="Look up a player by Player ID and Zone ID",
    responses={501: {"description": "No permitted public source exposes player statistics"}},
)
async def player_lookup(
    service: Annotated[PlayerService, Depends(get_player_service)],
    player_id: Annotated[str, Path(min_length=1, max_length=32, pattern=r"^\d+$")],
    zone_id: Annotated[str, Path(min_length=1, max_length=16, pattern=r"^\d+$")],
) -> ItemResponse[PlayerProfile]:
    profile = await service.lookup(player_id, zone_id)
    return ItemResponse(data=profile, meta=Meta())
