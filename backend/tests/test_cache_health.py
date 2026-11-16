"""Tests for the database cache tier and the provider-health log.

The cache tier is the cold half of the two-tier cache: the in-process TTL
cache is the hot tier, the database keeps the payload across a restart. The
health log records what actually happened on every upstream call.
"""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.v1.deps import get_db_session_factory
from app.db.base import Base
from app.db.models import ApiCacheEntry, ProviderHealthEvent
from app.db.repo import (
    cache_read,
    cache_write,
    recent_provider_health,
    record_provider_health,
)
from app.main import create_app


@pytest.fixture
def factory(tmp_path):
    """A throwaway SQLite database — no network, no app-global engine state."""
    engine = create_engine(f"sqlite:///{tmp_path / 'cache.db'}", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


# — Cache tier ————————————————————————————————————————————————————


def test_cache_write_then_read_returns_payload(factory):
    cache_write(factory, "catalog:v1", "rone_arena", [{"id": 1, "name": "Masha"}], ttl=60)
    assert cache_read(factory, "catalog:v1") == [{"id": 1, "name": "Masha"}]


def test_cache_read_miss_returns_none(factory):
    assert cache_read(factory, "nothing-here") is None


def test_expired_entry_is_not_returned(factory):
    """A TTL of zero means the entry is already stale."""
    cache_write(factory, "rankings:v1", "rone_arena", [{"id": 1}], ttl=0)
    assert cache_read(factory, "rankings:v1") is None


def test_expired_entry_is_purged_on_read(factory):
    cache_write(factory, "rankings:v1", "rone_arena", [{"id": 1}], ttl=0)
    cache_read(factory, "rankings:v1")
    with factory() as session:
        rows = list(session.scalars(select(ApiCacheEntry)))
    assert rows == []


def test_cache_write_refreshes_existing_entry(factory):
    cache_write(factory, "k", "rone_arena", [{"v": 1}], ttl=60)
    cache_write(factory, "k", "rone_arena", [{"v": 2}], ttl=60)
    assert cache_read(factory, "k") == [{"v": 2}]
    with factory() as session:
        rows = list(session.scalars(select(ApiCacheEntry)))
    assert len(rows) == 1


def test_cache_entry_records_expiry_and_provider(factory):
    cache_write(factory, "k", "mlbbdex", [{"v": 1}], ttl=120)
    with factory() as session:
        row = session.scalar(select(ApiCacheEntry))
    assert row is not None
    assert row.provider == "mlbbdex"
    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    assert 0 < (expires_at - now).total_seconds() <= 120


# — Provider health log ——————————————————————————————————————————


def test_record_provider_health_appends_an_event(factory):
    record_provider_health(
        factory,
        provider="rone_arena",
        endpoint="/api/heroes",
        status="ok",
        status_code=200,
        latency_ms=142,
    )
    events = recent_provider_health(factory)
    assert len(events) == 1
    event = events[0]
    assert event.provider == "rone_arena"
    assert event.endpoint == "/api/heroes"
    assert event.status == "ok"
    assert event.status_code == 200
    assert event.latency_ms == 142
    assert event.error_code is None


def test_provider_health_records_failures_with_error_code(factory):
    record_provider_health(
        factory,
        provider="rone_arena",
        endpoint="/api/esports/id/standings",
        status="error",
        status_code=503,
        error_code="http_503",
    )
    event = recent_provider_health(factory)[0]
    assert event.status == "error"
    assert event.status_code == 503
    assert event.error_code == "http_503"


def test_provider_health_is_newest_first_and_limited(factory):
    for i in range(5):
        record_provider_health(
            factory, provider="rone_arena", endpoint=f"/api/{i}", status="ok", status_code=200
        )
    events = recent_provider_health(factory, limit=3)
    assert len(events) == 3
    assert [e.endpoint for e in events] == ["/api/4", "/api/3", "/api/2"]


# — Endpoint ————————————————————————————————————————————————————————


def test_health_history_endpoint_returns_recorded_events(factory):
    record_provider_health(
        factory,
        provider="mlbbdex",
        endpoint="/api/v1/heroes",
        status="ok",
        status_code=200,
        latency_ms=88,
    )

    app = create_app()
    app.dependency_overrides[get_db_session_factory] = lambda: factory
    with TestClient(app) as client:
        resp = client.get("/api/v1/health/history")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["count"] == 1
    event = body["events"][0]
    assert event["provider"] == "mlbbdex"
    assert event["endpoint"] == "/api/v1/heroes"
    assert event["status"] == "ok"
    assert event["statusCode"] == 200
    assert event["latencyMs"] == 88
    assert event["checkedAt"]


def test_health_history_endpoint_is_empty_without_events(factory):
    app = create_app()
    app.dependency_overrides[get_db_session_factory] = lambda: factory
    with TestClient(app) as client:
        resp = client.get("/api/v1/health/history")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "count": 0, "events": []}


def test_health_history_limit_is_validated(factory):
    app = create_app()
    app.dependency_overrides[get_db_session_factory] = lambda: factory
    with TestClient(app) as client:
        assert client.get("/api/v1/health/history?limit=0").status_code == 422
        assert client.get("/api/v1/health/history?limit=500").status_code == 422
