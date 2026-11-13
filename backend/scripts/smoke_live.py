"""Live smoke test: exercises the real providers over the network.

Not part of the automated suite (which is fully offline). Run manually:

    .venv\\Scripts\\python.exe scripts\\smoke_live.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.core.errors import NotSupportedError  # noqa: E402
from app.integrations.provider_factory import get_providers  # noqa: E402
from app.services.hero_service import HeroService  # noqa: E402
from app.services.player_service import PlayerService  # noqa: E402


async def main() -> int:
    settings = get_settings()
    providers = get_providers()
    heroes = HeroService(providers, settings)
    players = PlayerService(providers)
    try:
        catalog = await heroes.catalog()
        print(f"[catalog] {len(catalog)} heroes; e.g. "
              + ", ".join(f"{h.name}#{h.id}({h.roles[0] if h.roles else '?'})" for h in catalog[:5]))

        rankings = await heroes.rankings(days=7, rank="all", sort_field="win_rate")
        print(f"[rankings] {len(rankings)} rows; top: "
              + ", ".join(f"{r.name} {r.win_rate*100:.1f}% (tier {r.tier})" for r in rankings[:3]))

        detail = await heroes.hero("khufra")
        print(f"[detail] {detail.name} id={detail.id} roles={detail.roles} lanes={detail.lanes}")
        print(f"[detail] skills={len(detail.skills)} strong={detail.strong_against[:3]} weak={detail.weak_against[:3]}")
        if detail.rank_stat:
            print(f"[detail] win={detail.rank_stat.win_rate*100:.1f}% ban={detail.rank_stat.ban_rate*100:.1f}%")

        try:
            await players.lookup("123456789", "1234")
            print("[player] UNEXPECTED: lookup succeeded")
            return 1
        except NotSupportedError as exc:
            print(f"[player] correctly unsupported -> {exc.code}: {exc.message}")

        print("\nLIVE SMOKE OK")
        return 0
    finally:
        await providers.aclose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
