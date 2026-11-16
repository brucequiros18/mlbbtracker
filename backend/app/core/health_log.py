"""Provider health log sink.

The integrations layer must not depend on the database, so it publishes call
outcomes here and the application wires a database-backed recorder at startup.
When no sink is installed (unit tests, scripts) the calls are simply dropped.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from urllib.parse import urlparse

from app.core.logging import get_logger

logger = get_logger(__name__)

HealthSink = Callable[..., None]

_sink: HealthSink | None = None

_PROVIDERS_BY_HOST = {
    "mlbbdex.com": "mlbbdex",
    "arena.rone.dev": "rone_arena",
    "arena.fastapicloud.dev": "rone_arena",
}


def provider_for_url(url: str) -> str:
    """Map a provider URL to a stable provider name."""
    host = urlparse(url).netloc.lower()
    for known, name in _PROVIDERS_BY_HOST.items():
        if known in host:
            return name
    return "unknown"


def set_health_sink(sink: HealthSink | None) -> None:
    """Install (or clear) the recorder that receives health events."""
    global _sink
    _sink = sink


def report(
    url: str,
    *,
    status: str,
    status_code: int | None = None,
    error_code: str | None = None,
    started_at: float | None = None,
) -> None:
    """Publish one provider call outcome (never raises)."""
    if _sink is None:
        return
    latency_ms = None
    if started_at is not None:
        latency_ms = int((time.monotonic() - started_at) * 1000)
    try:
        _sink(
            provider=provider_for_url(url),
            endpoint=urlparse(url).path,
            status=status,
            status_code=status_code,
            latency_ms=latency_ms,
            error_code=error_code,
        )
    except Exception:  # noqa: BLE001 — health logging must never break a request
        logger.exception("health log write failed")
