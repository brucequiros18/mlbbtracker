"""API v1 router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import app_release, auth, esports, health, heroes, players

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(heroes.router)
api_router.include_router(players.router)
api_router.include_router(esports.router)
api_router.include_router(app_release.router)
