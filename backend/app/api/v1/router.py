"""API v1 router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health, heroes, players

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(heroes.router)
api_router.include_router(players.router)
