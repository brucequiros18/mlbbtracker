"""Application configuration.

Values can be overridden with environment variables prefixed ``MLBB_``
(for example ``MLBB_RONE_BASE_URL``) or via a ``.env`` file.
"""

from __future__ import annotations

from functools import lru_cache

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

    cors_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
