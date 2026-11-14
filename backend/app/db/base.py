"""Engine and session factory, built lazily from settings.

The engine is created on first use (not at import time) so that unit tests
which never touch the database pay no cost and so overriding the URL via
``MLBB_DATABASE_URL`` works before anything connects.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    engine = create_engine(url, future=True)
    # SQLite needs this pragma per connection to enforce unique constraints
    # under concurrent writes.
    if url.startswith("sqlite"):
        def _set_sqlite_pragma(dbapi_connection, _record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        listen(engine, "connect", _set_sqlite_pragma)
    return engine


@lru_cache
def get_session_factory() -> Callable[[], Session]:
    engine = get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
