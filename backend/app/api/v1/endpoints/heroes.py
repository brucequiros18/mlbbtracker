"""Hero endpoints. All data is real, sourced from the enabled providers."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_hero_service
from app.schemas.common import (
    DEX_SOURCE,
    RONE_SOURCE,
    ItemResponse,
    ListResponse,
    Meta,
)
from app.schemas.hero import HeroDetail, HeroRanking, HeroSummary
from app.services.hero_service import HeroService

router = APIRouter(prefix="/heroes", tags=["heroes"])

# Query strings arrive as text; a string Literal validates the allowed windows
# without pydantic's Literal-vs-int coercion pitfall.
RankWindow = Literal["1", "3", "7", "15", "30"]
RankTier = Literal["all", "epic", "legend", "mythic", "honor", "glory"]
SortField = Literal["win_rate", "ban_rate", "pick_rate"]


@router.get("", response_model=ListResponse[HeroSummary], summary="List heroes")
async def list_heroes(
    service: Annotated[HeroService, Depends(get_hero_service)],
    role: Annotated[str | None, Query(description="Filter by role, e.g. Tank")] = None,
    lane: Annotated[str | None, Query(description="Filter by lane, e.g. Roam")] = None,
) -> ListResponse[HeroSummary]:
    heroes = await service.catalog(role=role, lane=lane)
    return ListResponse(
        data=heroes,
        meta=Meta(count=len(heroes), sources=[RONE_SOURCE, DEX_SOURCE]),
    )


@router.get(
    "/rankings",
    response_model=ListResponse[HeroRanking],
    summary="Hero win/ban/pick rankings",
)
async def hero_rankings(
    service: Annotated[HeroService, Depends(get_hero_service)],
    days: Annotated[RankWindow, Query(description="Window in days")] = "7",
    rank: Annotated[RankTier, Query(description="Rank tier filter")] = "all",
    sort: Annotated[SortField, Query(description="Sort field")] = "win_rate",
) -> ListResponse[HeroRanking]:
    rows = await service.rankings(days=int(days), rank=rank, sort_field=sort)
    return ListResponse(
        data=rows,
        meta=Meta(count=len(rows), sources=[RONE_SOURCE, DEX_SOURCE]),
    )


@router.get(
    "/{identifier}",
    response_model=ItemResponse[HeroDetail],
    summary="Hero detail by id, slug or name",
)
async def hero_detail(
    identifier: str,
    service: Annotated[HeroService, Depends(get_hero_service)],
) -> ItemResponse[HeroDetail]:
    hero = await service.hero(identifier)
    return ItemResponse(data=hero, meta=Meta(sources=[RONE_SOURCE, DEX_SOURCE]))
