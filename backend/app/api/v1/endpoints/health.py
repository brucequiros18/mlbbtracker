"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
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
