"""Health endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db_session_factory
from app.core.config import get_settings
from app.db.repo import recent_provider_health
from app.integrations.provider_factory import get_providers
from app.services.health_service import health_payload, probe_providers

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness and capability summary")
async def health() -> dict:
    return await health_payload(get_settings(), get_providers())


@router.get("/health/providers", summary="Live provider reachability probe")
async def providers_health() -> dict:
    results = await probe_providers(get_providers())
    return {"status": "ok", "providers": results}


@router.get(
    "/health/history",
    summary="Recorded provider call outcomes (from the database)",
)
async def providers_history(
    session_factory: Annotated[Callable[[], Session], Depends(get_db_session_factory)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict:
    """The provider health log — what actually happened, as recorded.

    Unlike `/health/providers` this does not call upstream; it returns the
    outcomes observed and stored by previous requests.
    """
    events = recent_provider_health(session_factory, limit=limit)
    return {
        "status": "ok",
        "count": len(events),
        "events": [
            {
                "provider": e.provider,
                "endpoint": e.endpoint,
                "status": e.status,
                "statusCode": e.status_code,
                "latencyMs": e.latency_ms,
                "errorCode": e.error_code,
                "checkedAt": e.checked_at.isoformat() if e.checked_at else None,
            }
            for e in events
        ],
    }
