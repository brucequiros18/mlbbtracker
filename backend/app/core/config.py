"""Application configuration.

Values can be overridden with environment variables prefixed ``MLBB_``
(for example ``MLBB_RONE_BASE_URL``) or via a ``.env`` file.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MLBB_",
        extra="ignore",
    )

    app_name: str = "MLBB Tracker API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # Provider endpoints (real, verified in docs/API_DOCUMENTATION.md).
    rone_base_url: str = "https://arena.rone.dev/api"
    mlbbdex_base_url: str = "https://mlbbdex.com/api/v1"

    # Provider toggles. At least one hero provider must be enabled.
    enable_rone: bool = True
    enable_mlbbdex: bool = True
    # Player data requires an authenticated source, which is not enabled.
    enable_player_lookup: bool = False

    http_timeout: float = 15.0
    http_user_agent: str = "mlbb-tracker-backend/0.1 (+https://example.local)"

    # Cache TTLs (seconds).
    cache_ttl_catalog: int = 6 * 60 * 60
    cache_ttl_rankings: int = 60 * 60
    cache_ttl_detail: int = 6 * 60 * 60
    cache_ttl_health: int = 60

    # Database. Default is a local SQLite file for development; point this at
    # a Supabase/Postgres URL for production (models/migrations are shared).
    database_url: str = "sqlite:///./mlbb_tracker.db"

    cors_origins: list[str] = ["*"]

    # Static web build to serve alongside the API (the Flutter web app).
    # Empty = auto-detect `<repo>/mobile/build/web` when it exists.
    web_root: str = ""

    # Published app releases (APK + latest.json manifest), served at
    # /download and /downloads/<file>. Empty = auto-detect `<repo>/releases`.
    releases_dir: str = ""

    # Google sign-in - the app's only credential. The value is the OAuth 2.0
    # *web* client ID from Google Cloud Console; it is public (it ships to the
    # browser), so the API exposes it via GET /api/v1/auth/config.
    # Empty = not configured: sign-in answers 503 GOOGLE_NOT_CONFIGURED and the
    # app shows that state instead of a button that cannot work.
    google_client_id: str = ""

    # How long an app account session stays valid (sliding, refreshed on use).
    user_session_ttl_days: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: Any) -> Any:
        """Accept `MLBB_CORS_ORIGINS=https://a.com,https://b.com` as well as JSON."""
        if isinstance(value, str):
            parts = [p.strip() for p in value.split(",") if p.strip()]
            return parts or ["*"]
        return value

    def resolved_web_root(self) -> Path | None:
        """Directory holding the Flutter web build, if one is available."""
        if self.web_root:
            path = Path(self.web_root).expanduser()
            return path if path.is_dir() else None
        # backend/app/core/config.py -> repo root is three parents up.
        repo_root = Path(__file__).resolve().parents[3]
        candidate = repo_root / "mobile" / "build" / "web"
        return candidate if candidate.is_dir() else None

    def resolved_releases_dir(self) -> Path:
        """Directory holding published app releases (may not exist yet)."""
        if self.releases_dir:
            return Path(self.releases_dir).expanduser()
        # backend/app/core/config.py -> repo root is three parents up.
        return Path(__file__).resolve().parents[3] / "releases"


@lru_cache
def get_settings() -> Settings:
    return Settings()
