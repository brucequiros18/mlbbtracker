"""Esports endpoints: professional league standings (MPL ID/PH/MY/KH)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_esports_service
from app.schemas.common import ListResponse, Meta, RONE_SOURCE
from app.schemas.esports import EsportsStandingRow
from app.services.esports_service import EsportsService

router = APIRouter(prefix="/esports", tags=["esports"])

League = Literal["id", "ph", "my", "kh"]


@router.get(
    "/{league}/standings",
    response_model=ListResponse[EsportsStandingRow],
    summary="Regular-season standings for a professional league",
)
async def league_standings(
    league: League,
    service: Annotated[EsportsService, Depends(get_esports_service)],
) -> ListResponse[EsportsStandingRow]:
    rows = await service.standings(league)
    return ListResponse(
        data=[EsportsStandingRow.from_domain(r) for r in rows],
        meta=Meta(count=len(rows), sources=[RONE_SOURCE]),
    )
