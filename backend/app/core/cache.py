"""A minimal in-process TTL cache.

Good enough for a single instance and for development. It is deliberately
behind a tiny interface so a Redis-backed implementation can be dropped in
later without touching the services.
"""

from __future__ import annotations

import threading
import time
from typing import Any


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < time.monotonic():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> dict[str, int]:
        with self._lock:
            now = time.monotonic()
            live = sum(1 for exp, _ in self._store.values() if exp >= now)
            return {"entries": live, "expired": len(self._store) - live}


cache = TTLCache()
