"""Player endpoints.

Anonymous lookup by ID/zone returns 501: no public source serves another
player's statistics without consent.

Connected mode (real data, consented):
  1. POST /players/connect/start   {playerId, zoneId} -> in-game verification code
  2. POST /players/connect/verify  {playerId, zoneId, code} -> app session token
  3. GET  /players/me/{profile|stats|matches|heroes}  with `Authorization: Bearer <token>`

The provider JWT never leaves the backend.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.deps import get_player_service
from app.core.errors import ProviderAuthError
from app.schemas.common import ItemResponse, ListResponse, Meta
from app.schemas.player import (
    ConnectRequest,
    ConnectStart,
    ConnectVerify,
    ConnectVerifyRequest,
    FrequentHero,
    PlayerMatch,
    PlayerMatchesPage,
    PlayerProfile,
    PlayerStats,
)
from app.services.player_service import PlayerService

router = APIRouter(prefix="/players", tags=["players"])

_bearer = HTTPBearer(auto_error=False, description="Opaque app session token from /players/connect/verify")


def get_session_token(
    creds: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
) -> str:
    if creds is None or not creds.credentials:
        raise ProviderAuthError(
            "Connect your MLBB account first: POST /players/connect/start, then /connect/verify."
        )
    return creds.credentials


SessionToken = Annotated[str, Depends(get_session_token)]


@router.post(
    "/connect/start",
    response_model=ItemResponse[ConnectStart],
    summary="Send a one-time verification code to your in-game mailbox",
)
async def connect_start(
    service: Annotated[PlayerService, Depends(get_player_service)],
    payload: ConnectRequest,
) -> ItemResponse[ConnectStart]:
    await service.start_connect(payload.player_id, payload.zone_id)
    return ItemResponse(
        data=ConnectStart(
            sent=True,
            message="A verification code was sent to your in-game mailbox. It expires in a few minutes.",
        ),
        meta=Meta(),
    )


@router.post(
    "/connect/verify",
    response_model=ItemResponse[ConnectVerify],
    summary="Exchange the in-game code for a backend session token",
)
async def connect_verify(
    service: Annotated[PlayerService, Depends(get_player_service)],
    payload: ConnectVerifyRequest,
) -> ItemResponse[ConnectVerify]:
    session_key, info = await service.verify_connect(
        payload.player_id, payload.zone_id, payload.code
    )
    return ItemResponse(
        data=ConnectVerify(
            session_token=session_key, player=PlayerProfile.from_domain(info)
        ),
        meta=Meta(),
    )


@router.post("/disconnect", summary="Forget the connected account on this server")
async def disconnect(
    service: Annotated[PlayerService, Depends(get_player_service)],
    session_key: SessionToken,
) -> ItemResponse[dict]:
    await service.disconnect(session_key)
    return ItemResponse(data={"disconnected": True}, meta=Meta())


@router.get(
    "/me/profile",
    response_model=ItemResponse[PlayerProfile],
    summary="Connected player's profile",
)
async def my_profile(
    service: Annotated[PlayerService, Depends(get_player_service)],
    session_key: SessionToken,
) -> ItemResponse[PlayerProfile]:
    info = await service.profile(session_key)
    return ItemResponse(data=PlayerProfile.from_domain(info), meta=Meta())


@router.get(
    "/me/stats",
    response_model=ItemResponse[PlayerStats],
    summary="Connected player's aggregate statistics",
)
async def my_stats(
    service: Annotated[PlayerService, Depends(get_player_service)],
    session_key: SessionToken,
) -> ItemResponse[PlayerStats]:
    stats = await service.stats(session_key)
    return ItemResponse(data=PlayerStats.from_domain(stats), meta=Meta())


@router.get(
    "/me/matches",
    response_model=ItemResponse[PlayerMatchesPage],
    summary="Connected player's recent matches",
)
async def my_matches(
    service: Annotated[PlayerService, Depends(get_player_service)],
    session_key: SessionToken,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: Annotated[str | None, Query()] = None,
) -> ItemResponse[PlayerMatchesPage]:
    page = await service.matches(session_key, limit=limit, cursor=cursor)
    return ItemResponse(
        data=PlayerMatchesPage(
            data=[PlayerMatch.from_domain(m) for m in page.matches],
            next_cursor=page.next_cursor,
            has_next=page.has_next,
        ),
        meta=Meta(count=len(page.matches)),
    )


@router.get(
    "/me/heroes",
    response_model=ListResponse[FrequentHero],
    summary="Connected player's most-played heroes",
)
async def my_heroes(
    service: Annotated[PlayerService, Depends(get_player_service)],
    session_key: SessionToken,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> ListResponse[FrequentHero]:
    heroes = await service.frequent_heroes(session_key, limit=limit)
    return ListResponse(
        data=[FrequentHero.from_domain(h) for h in heroes],
        meta=Meta(count=len(heroes)),
    )


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
