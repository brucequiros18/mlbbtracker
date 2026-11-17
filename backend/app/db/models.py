"""ORM models.

Only data we genuinely record is stored here — snapshots of provider ranking
data as it was observed. Nothing is ever synthesized: if a hero had no
ranking entry on a given day, it has no row for that day.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HeroSnapshot(Base):
    """A daily observation of a hero's rank-window statistics.

    Rows are written whenever the backend fetches the 7-day rankings from the
    live provider and no snapshot exists yet for (hero, window, day).
    """

    __tablename__ = "hero_snapshots"
    __table_args__ = (
        UniqueConstraint("hero_id", "days", "captured_on", name="uq_hero_day_window"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    hero_name: Mapped[str] = mapped_column(String(64), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    captured_on: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False)
    ban_rate: Mapped[float] = mapped_column(Float, nullable=False)
    pick_rate: Mapped[float] = mapped_column(Float, nullable=False)
    tier: Mapped[str | None] = mapped_column(String(16), nullable=True)
    rank_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PlayerSession(Base):
    """A consented player connection.

    The provider JWT is stored server-side only; the app holds an opaque
    session key whose SHA-256 hash is what appears in `session_hash`.
    """

    __tablename__ = "player_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    provider_token: Mapped[str] = mapped_column(Text, nullable=False)
    role_id: Mapped[str] = mapped_column(String(32), nullable=False)
    zone_id: Mapped[str] = mapped_column(String(16), nullable=False)
    ign: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )




class User(Base):
    """An app account, created by signing in with Google.

    Google is the only credential. ``google_sub`` is the stable subject of a
    verified Google ID token, so it is the identity key - never the email.

    ``username``, ``mlbb_id`` and ``password_hash`` are app-only profile data:

    * the MLBB ID is **self-declared and never verified** against Moonton;
    * the password is a salted scrypt hash that never leaves this database. It
      is not a sign-in method and is never sent to Moonton - it only confirms
      changes to the profile (see ``PATCH /api/v1/auth/me``).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    google_sub: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    google_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Chosen by the player after the Google sign-in. NULL until then, which is
    # how the app knows the profile still has to be completed.
    username: Mapped[str | None] = mapped_column(
        String(24), unique=True, index=True, nullable=True
    )
    mlbb_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class UserSession(Base):
    """A signed-in app session (Google-authenticated).

    The app holds an opaque bearer token; only its SHA-256 hash is stored here,
    mirroring the consented player-session pattern.
    """

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class ApiCacheEntry(Base):
    """Persistent provider-response cache (survives a backend restart).

    The in-process TTL cache is the hot tier; this table is the cold tier that
    keeps a restart from re-fetching the full hero catalog from upstream.
    """

    __tablename__ = "api_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict | list] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class ProviderHealthEvent(Base):
    """One observed provider call: reachability, latency and status."""

    __tablename__ = "provider_health"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # ok | error
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(48), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
