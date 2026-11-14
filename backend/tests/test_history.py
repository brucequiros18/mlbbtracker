"""Persistence tests: snapshot recording and the /history read path.

Uses a throwaway SQLite file — no network, no app-global engine state.
"""

from __future__ import annotations

import datetime as dt
from functools import partial

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.v1.deps import get_hero_service
from app.core.config import get_settings
from app.db.base import Base
from app.db.models import HeroSnapshot
from app.db.repo import history_for_hero, record_rankings
from app.integrations.models import RankingEntry
from app.main import create_app
from app.services.hero_service import HeroService


@pytest.fixture
def db_client(tmp_path, fake_providers):
    """App wired to a temp database with recording enabled."""
    engine = create_engine(f"sqlite:///{tmp_path / 't.db'}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    app = create_app()
    app.dependency_overrides[get_hero_service] = lambda: HeroService(
        fake_providers,
        get_settings(),
        recorder=partial(record_rankings, factory),
        session_factory=factory,
    )
    with TestClient(app) as c:
        yield c, factory


def test_rankings_fetch_records_snapshots(db_client):
    client, factory = db_client
    resp = client.get("/api/v1/heroes/rankings")
    assert resp.status_code == 200
    with factory() as s:
        rows = list(s.scalars(select(HeroSnapshot)))
    assert len(rows) >= 2
    first = rows[0]
    assert first.days == 7
    assert first.captured_on == dt.datetime.now(dt.timezone.utc).date()
    assert first.win_rate > 0


def test_record_is_idempotent_per_day(db_client):
    client, factory = db_client
    client.get("/api/v1/heroes/rankings")
    entry = RankingEntry(id=999, name="Test Hero", slug=None, head_image=None,
                         win_rate=0.9, ban_rate=0.1, pick_rate=0.05, tier=None)
    assert record_rankings(factory, [entry]) == 1  # new hero id -> 1 new row
    assert record_rankings(factory, [entry]) == 0  # same day again -> nothing


def test_history_endpoint_returns_recorded_points(db_client):
    client, _factory = db_client
    client.get("/api/v1/heroes/rankings")  # triggers recording
    resp = client.get("/api/v1/heroes/masha/history")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["count"] >= 1
    point = body["data"][0]
    assert "capturedOn" in point
    assert point["winRate"] > 0
    assert body["meta"]["sources"] == []  # our own recorded data, no upstream


def test_history_empty_until_recorded(tmp_path, fake_providers):
    engine = create_engine(f"sqlite:///{tmp_path / 't.db'}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    app = create_app()
    app.dependency_overrides[get_hero_service] = lambda: HeroService(
        fake_providers, get_settings(), recorder=None, session_factory=factory
    )
    with TestClient(app) as client:
        resp = client.get("/api/v1/heroes/masha/history")
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["count"] == 0
        assert "No snapshots recorded yet" in body["meta"]["note"]


def test_history_orders_oldest_first(db_client):
    client, factory = db_client
    client.get("/api/v1/heroes/rankings")
    yesterday = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)
    entry = RankingEntry(id=88, name="Masha", slug="masha", head_image=None,
                         win_rate=0.5, ban_rate=0.02, pick_rate=0.01, tier=None)
    record_rankings(factory, [entry], days=7, captured_on=yesterday)
    rows = history_for_hero(factory, 88)
    dates = [r.captured_on for r in rows]
    assert dates == sorted(dates)
    assert rows[0].captured_on == yesterday
