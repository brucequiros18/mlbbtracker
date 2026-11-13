"""Shared HTTP client factory and safe JSON helpers for provider adapters."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ProviderError, ProviderUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        headers={"user-agent": settings.http_user_agent, "accept": "application/json"},
        follow_redirects=True,
    )


async def get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
) -> Any:
    """GET ``url`` and return parsed JSON, translating failures into AppErrors."""
    try:
        response = await client.get(url, params=params)
    except httpx.TimeoutException as exc:  # pragma: no cover - network dependent
        logger.warning("provider timeout url=%s", url)
        raise ProviderUnavailableError("The upstream provider timed out.") from exc
    except httpx.HTTPError as exc:  # pragma: no cover - network dependent
        logger.warning("provider transport error url=%s err=%s", url, exc)
        raise ProviderUnavailableError("The upstream provider is unreachable.") from exc

    if response.status_code >= 500:
        raise ProviderUnavailableError(
            f"Provider returned {response.status_code}."
        )
    if response.status_code >= 400:
        raise ProviderError(f"Provider rejected the request ({response.status_code}).")

    try:
        return response.json()
    except ValueError as exc:
        raise ProviderError("Provider returned a non-JSON response.") from exc
