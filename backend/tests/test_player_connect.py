"""Consented player sign-in flow — offline tests with a fake provider."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.deps import get_player_service
from app.db.base import Base
from app.db.repo import find_session
from app.main import create_app
from app.services.player_service import PlayerService


@pytest.fixture
def connect_client(tmp_path, fake_providers):
    engine = create_engine(f"sqlite:///{tmp_path / 'p.db'}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    app = create_app()
    app.dependency_overrides[get_player_service] = lambda: PlayerService(
        fake_providers, session_factory=factory
    )
    with TestClient(app) as c:
        yield c, factory


def _connect(client) -> str:
    start = client.post(
        "/api/v1/players/connect/start",
        json={"playerId": "123456789", "zoneId": "1234"},
    )
    assert start.status_code == 200, start.text
    verify = client.post(
        "/api/v1/players/connect/verify",
        json={"playerId": "123456789", "zoneId": "1234", "code": "111111"},
    )
    assert verify.status_code == 200, verify.text
    return verify.json()["data"]["sessionToken"]


def test_connect_start_sends_code(connect_client):
    client, _ = connect_client
    resp = client.post(
        "/api/v1/players/connect/start",
        json={"playerId": "123456789", "zoneId": "1234"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["sent"] is True


def test_connect_start_unknown_player(connect_client):
    client, _ = connect_client
    resp = client.post(
        "/api/v1/players/connect/start",
        json={"playerId": "999999999", "zoneId": "1234"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "PROVIDER_AUTH_REQUIRED"


def test_verify_rejects_wrong_code(connect_client):
    client, _ = connect_client
    resp = client.post(
        "/api/v1/players/connect/verify",
        json={"playerId": "123456789", "zoneId": "1234", "code": "999999"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "PROVIDER_AUTH_REQUIRED"


def test_verify_returns_session_and_stores_hashed_key(connect_client):
    client, factory = connect_client
    token = _connect(client)
    assert token
    row = find_session(factory, token)
    assert row is not None
    # The raw key is never stored; only its hash.
    assert row.session_hash != token
    assert row.provider_token == "fake-provider-jwt"


def test_profile_requires_token(connect_client):
    client, _ = connect_client
    resp = client.get("/api/v1/players/me/profile")
    assert resp.status_code == 401
    assert resp.json()["code"] == "PROVIDER_AUTH_REQUIRED"


def test_profile_returns_real_shape(connect_client):
    client, _ = connect_client
    token = _connect(client)
    resp = client.get(
        "/api/v1/players/me/profile", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ign"] == "TestPlayer"
    assert data["playerId"] == "123456789"
    assert data["rankLevel"] == 7


def test_stats_mapping(connect_client):
    client, _ = connect_client
    token = _connect(client)
    data = client.get(
        "/api/v1/players/me/stats", headers={"Authorization": f"Bearer {token}"}
    ).json()["data"]
    assert data["totalMatches"] == 100
    assert data["wins"] == 60
    assert data["winRate"] == 0.6
    assert data["mvpCount"] == 14
    assert data["winStreak"] == 7


def test_matches_mapping_and_pagination(connect_client):
    client, _ = connect_client
    token = _connect(client)
    body = client.get(
        "/api/v1/players/me/matches?limit=2", headers={"Authorization": f"Bearer {token}"}
    ).json()
    page = body["data"]
    assert page["hasNext"] is True
    assert page["nextCursor"] == "cursor-2"
    first = page["data"][0]
    assert first["won"] is True
    assert first["mvp"] is True
    assert first["kills"] == 8 and first["assists"] == 5
    assert first["kda"] == 6.5
    assert page["data"][1]["won"] is False


def test_frequent_heroes(connect_client):
    client, _ = connect_client
    token = _connect(client)
    body = client.get(
        "/api/v1/players/me/heroes", headers={"Authorization": f"Bearer {token}"}
    ).json()
    assert body["meta"]["count"] == 1
    assert body["data"][0]["heroName"] == "Masha"
    assert body["data"][0]["winRate"] == 0.65


def test_disconnect_revokes_session(connect_client):
    client, _ = connect_client
    token = _connect(client)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/players/disconnect", headers=headers).status_code == 200
    assert client.get("/api/v1/players/me/profile", headers=headers).status_code == 401


def test_connect_validates_numeric_ids(connect_client):
    client, _ = connect_client
    resp = client.post(
        "/api/v1/players/connect/start",
        json={"playerId": "abc", "zoneId": "1234"},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"
