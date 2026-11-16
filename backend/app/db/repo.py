"""Repository functions for recorded snapshots and player sessions."""

from __future__ import annotations

import datetime as dt
import hashlib
from collections.abc import Callable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ApiCacheEntry, HeroSnapshot, PlayerSession, ProviderHealthEvent
from app.integrations.models import RankingEntry


def record_rankings(
    session_factory: Callable[[], Session],
    rows: Sequence[RankingEntry],
    *,
    days: int = 7,
    captured_on: dt.date | None = None,
) -> int:
    """Persist one snapshot per hero per day, idempotently.

    Re-running on the same day inserts nothing (unique constraint + existence
    check), so scheduled refreshes are safe. Returns the number of new rows.
    """
    if not rows:
        return 0
    day = captured_on or dt.datetime.now(dt.timezone.utc).date()
    hero_ids = [r.id for r in rows if r.id]
    with session_factory() as session:
        existing = set(
            session.scalars(
                select(HeroSnapshot.hero_id).where(
                    HeroSnapshot.days == days,
                    HeroSnapshot.captured_on == day,
                    HeroSnapshot.hero_id.in_(hero_ids),
                )
            )
        )
        fresh = [
            HeroSnapshot(
                hero_id=row.id,
                hero_name=row.name,
                days=days,
                captured_on=day,
                win_rate=round(row.win_rate, 6),
                ban_rate=round(row.ban_rate, 6),
                pick_rate=round(row.pick_rate, 6),
                tier=row.tier,
                rank_position=position,
            )
            for position, row in enumerate(rows, start=1)
            if row.id and row.id not in existing
        ]
        if not fresh:
            return 0
        session.add_all(fresh)
        session.commit()
        return len(fresh)


def history_for_hero(
    session_factory: Callable[[], Session],
    hero_id: int,
    *,
    days: int = 7,
) -> list[HeroSnapshot]:
    """All recorded snapshots for a hero, oldest first."""
    with session_factory() as session:
        return list(
            session.scalars(
                select(HeroSnapshot)
                .where(HeroSnapshot.hero_id == hero_id, HeroSnapshot.days == days)
                .order_by(HeroSnapshot.captured_on.asc(), HeroSnapshot.id.asc())
            )
        )


# — Provider response cache (cold tier) ———————————————————————————


def cache_read(
    session_factory: Callable[[], Session], key: str
) -> dict | list | None:
    """Return a cached payload if present and not expired, else None."""
    now = dt.datetime.now(dt.timezone.utc)
    with session_factory() as session:
        row = session.scalar(select(ApiCacheEntry).where(ApiCacheEntry.cache_key == key))
        if row is None:
            return None
        expires_at = row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=dt.timezone.utc)
        if expires_at <= now:
            session.delete(row)
            session.commit()
            return None
        return row.payload


def cache_write(
    session_factory: Callable[[], Session],
    key: str,
    provider: str,
    payload: dict | list,
    ttl: int,
) -> None:
    """Store (or refresh) a cached payload with a TTL in seconds."""
    now = dt.datetime.now(dt.timezone.utc)
    with session_factory() as session:
        row = session.scalar(select(ApiCacheEntry).where(ApiCacheEntry.cache_key == key))
        if row is None:
            row = ApiCacheEntry(cache_key=key, provider=provider, payload=payload)
            session.add(row)
        row.provider = provider
        row.payload = payload
        row.expires_at = now + dt.timedelta(seconds=ttl)
        row.created_at = now
        session.commit()


# — Provider health log ——————————————————————————————————————————


def record_provider_health(
    session_factory: Callable[[], Session],
    *,
    provider: str,
    endpoint: str,
    status: str,
    status_code: int | None = None,
    latency_ms: int | None = None,
    error_code: str | None = None,
) -> None:
    """Append one provider call outcome to the health log."""
    with session_factory() as session:
        session.add(
            ProviderHealthEvent(
                provider=provider,
                endpoint=endpoint,
                status=status,
                status_code=status_code,
                latency_ms=latency_ms,
                error_code=error_code,
            )
        )
        session.commit()


def recent_provider_health(
    session_factory: Callable[[], Session], *, limit: int = 50
) -> list[ProviderHealthEvent]:
    """Most recent health events, newest first."""
    with session_factory() as session:
        return list(
            session.scalars(
                select(ProviderHealthEvent)
                .order_by(ProviderHealthEvent.checked_at.desc(), ProviderHealthEvent.id.desc())
                .limit(limit)
            )
        )


# — Player sessions —————————————————————————————————————————————


def hash_session_key(key: str) -> str:
    """SHA-256 of the opaque app session key (the raw key is never stored)."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def save_session(
    session_factory: Callable[[], Session],
    *,
    session_key: str,
    provider_token: str,
    role_id: str,
    zone_id: str,
    ign: str | None,
) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    key_hash = hash_session_key(session_key)
    with session_factory() as session:
        existing = session.scalar(
            select(PlayerSession).where(PlayerSession.session_hash == key_hash)
        )
        if existing is not None:
            existing.provider_token = provider_token
            existing.ign = ign
            existing.last_seen_at = now
        else:
            session.add(
                PlayerSession(
                    session_hash=key_hash,
                    provider_token=provider_token,
                    role_id=role_id,
                    zone_id=zone_id,
                    ign=ign,
                    created_at=now,
                    last_seen_at=now,
                )
            )
        session.commit()


def find_session(
    session_factory: Callable[[], Session], session_key: str
) -> PlayerSession | None:
    with session_factory() as session:
        return session.scalar(
            select(PlayerSession).where(
                PlayerSession.session_hash == hash_session_key(session_key)
            )
        )


def touch_session(session_factory: Callable[[], Session], session_key: str) -> None:
    with session_factory() as session:
        row = session.scalar(
            select(PlayerSession).where(
                PlayerSession.session_hash == hash_session_key(session_key)
            )
        )
        if row is not None:
            row.last_seen_at = dt.datetime.now(dt.timezone.utc)
            session.commit()


def delete_session(session_factory: Callable[[], Session], session_key: str) -> None:
    with session_factory() as session:
        row = session.scalar(
            select(PlayerSession).where(
                PlayerSession.session_hash == hash_session_key(session_key)
            )
        )
        if row is not None:
            session.delete(row)
            session.commit()
