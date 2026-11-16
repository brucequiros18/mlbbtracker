"""Shared HTTP client factory and safe JSON helpers for provider adapters."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ProviderAuthError, ProviderError, ProviderUnavailableError
from app.core.health_log import report
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout),
        headers={"user-agent": settings.http_user_agent, "accept": "application/json"},
        follow_redirects=True,
    )


async def _request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    bearer: str | None = None,
) -> Any:
    headers = {"authorization": f"Bearer {bearer}"} if bearer else None
    started_at = time.monotonic()
    try:
        response = await client.request(method, url, params=params, json=json, headers=headers)
    except httpx.TimeoutException as exc:  # pragma: no cover - network dependent
        logger.warning("provider timeout url=%s", url)
        report(url, status="error", error_code="timeout", started_at=started_at)
        raise ProviderUnavailableError("The upstream provider timed out.") from exc
    except httpx.HTTPError as exc:  # pragma: no cover - network dependent
        logger.warning("provider transport error url=%s err=%s", url, exc)
        report(url, status="error", error_code="transport", started_at=started_at)
        raise ProviderUnavailableError("The upstream provider is unreachable.") from exc

    if response.status_code >= 400:
        report(
            url,
            status="error",
            status_code=response.status_code,
            error_code=f"http_{response.status_code}",
            started_at=started_at,
        )
    else:
        report(url, status="ok", status_code=response.status_code, started_at=started_at)

    if response.status_code == 401:
        raise ProviderAuthError(
            "The provider rejected the session token. It has expired or been revoked."
        )
    if response.status_code >= 500:
        raise ProviderUnavailableError(f"Provider returned {response.status_code}.")
    if response.status_code >= 400:
        raise ProviderError(f"Provider rejected the request ({response.status_code}).")

    try:
        return response.json()
    except ValueError as exc:
        raise ProviderError("Provider returned a non-JSON response.") from exc


async def get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    bearer: str | None = None,
) -> Any:
    """GET ``url`` and return parsed JSON, translating failures into AppErrors."""
    return await _request_json(client, "GET", url, params=params, bearer=bearer)


async def post_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    json: Any | None = None,
    bearer: str | None = None,
) -> Any:
    """POST ``url`` and return parsed JSON."""
    return await _request_json(client, "POST", url, json=json, bearer=bearer)
