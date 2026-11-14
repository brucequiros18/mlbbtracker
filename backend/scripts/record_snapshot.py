"""Record a snapshot of the live 7-day rankings into the local database.

Run from ``backend/``:

    .\\.venv\\Scripts\\python.exe scripts\\record_snapshot.py

Intended for a scheduled task (Task Scheduler / cron) so history accumulates
even when nobody is using the app. Safe to re-run: one row per hero per UTC day.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base, get_engine, get_session_factory  # noqa: E402
from app.db.models import HeroSnapshot  # noqa: E402  (register model metadata)
from app.db.repo import record_rankings  # noqa: E402
from app.integrations.provider_factory import get_providers  # noqa: E402


async def main() -> int:
    settings = get_settings()
    providers = get_providers()

    # Ensure tables exist even before the first Alembic upgrade (dev only;
    # production should run `alembic upgrade head`).
    Base.metadata.create_all(get_engine())

    if not providers.rone:
        print("No ranking provider enabled (set MLBB_ENABLE_RONE=true).")
        return 1

    entries = await providers.rone.fetch_rankings(days=7, rank="all", sort_field="win_rate")
    inserted = record_rankings(get_session_factory(), entries, days=7)
    print(f"provider entries: {len(entries)}; new snapshot rows: {inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
