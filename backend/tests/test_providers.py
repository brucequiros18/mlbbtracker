"""Adapter parsing and normalization tests using an httpx MockTransport.

These exercise the real adapters against realistic provider payloads without
any network access.
"""

from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.integrations.mlbbdex import MlbbDexProvider
from app.integrations.models import normalize_hero_name
from app.integrations.rone_arena import RoneArenaProvider


def test_normalize_hero_name():
    assert normalize_hero_name("Luo Yi") == "luoyi"
    assert normalize_hero_name("X.Borg") == "xborg"
    assert normalize_hero_name("Yi Sun-shin") == "yisunshin"
    assert normalize_hero_name("Khufra") == "khufra"


@pytest.mark.asyncio
async def test_rone_parses_refs_and_rankings():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/heroes/rank"):
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "message": "OK",
                    "data": {
                        "records": [
                            {
                                "data": {
                                    "main_hero": {"data": {"head": "h", "name": "Masha"}},
                                    "main_heroid": 88,
                                    "main_hero_win_rate": 0.611,
                                    "main_hero_ban_rate": 0.43,
                                    "main_hero_appearance_rate": 0.0055,
                                }
                            }
                        ]
                    },
                },
            )
        return httpx.Response(
            200,
            json={
                "code": 0,
                "message": "OK",
                "data": {
                    "total": 1,
                    "records": [
                        {
                            "data": {
                                "hero": {"data": {"head": "img", "name": "Khufra"}},
                                "hero_id": 78,
                                "relation": {"strong": {"target_hero_id": [24]}, "weak": {"target_hero_id": [87]}},
                            }
                        }
                    ],
                },
            },
        )

    settings = Settings()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RoneArenaProvider(client, settings)
        refs = await provider.fetch_hero_refs()
        rankings = await provider.fetch_rankings(days=7, rank="all")

    assert refs[0].id == 78
    assert refs[0].name == "Khufra"
    assert refs[0].strong_ids == [24]
    assert rankings[0].id == 88
    assert rankings[0].win_rate == pytest.approx(0.611)


@pytest.mark.asyncio
async def test_mlbbdex_parses_catalog_detail_and_rankings():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/rankings"):
            return httpx.Response(
                200,
                json={"data": {"heroes": [{"slug": "khufra", "name": "Khufra", "tier": "A+", "winRate": 54.6, "banRate": 2.0, "pickRate": 0.3}]}},
            )
        if path.endswith("/heroes/khufra"):
            return httpx.Response(
                200,
                json={"data": {"slug": "khufra", "name": "Khufra", "roles": ["Tank"], "lanes": ["Roam"], "skills": [{"name": "Spell Curse", "description": "desc"}]}},
            )
        return httpx.Response(
            200,
            json={"data": [{"slug": "khufra", "name": "Khufra", "roles": ["Tank"], "lanes": ["Roam"], "specialties": ["Initiator"]}]},
        )

    settings = Settings()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = MlbbDexProvider(client, settings)
        catalog = await provider.fetch_hero_catalog()
        detail = await provider.fetch_hero_detail("khufra")
        rankings = await provider.fetch_rankings()

    assert catalog[0].slug == "khufra"
    assert detail.skills[0].name == "Spell Curse"
    assert rankings[0].tier == "A+"
