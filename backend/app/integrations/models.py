"""Provider-neutral data shapes.

Every adapter converts its provider's raw JSON into these dataclasses, so the
service layer and the API never depend on a specific provider's schema.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


def normalize_hero_name(value: str) -> str:
    """Case/spacing/symbol-insensitive key used to join data across providers.

    ``"Luo Yi"`` -> ``"luoyi"``, ``"X.Borg"`` -> ``"xborg"``, ``"Yi Sun-shin"``
    -> ``"yisunshin"``.
    """
    return re.sub(r"[^a-z0-9]", "", value.lower())


@dataclass(slots=True)
class HeroRef:
    """Canonical hero identity: the real in-game numeric id plus a portrait."""

    id: int
    name: str
    head_image: str | None = None
    strong_ids: list[int] = field(default_factory=list)
    weak_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class HeroMeta:
    """Descriptive metadata (roles/lanes) sourced from the wiki-backed API."""

    slug: str
    name: str
    roles: list[str] = field(default_factory=list)
    lanes: list[str] = field(default_factory=list)
    specialties: list[str] = field(default_factory=list)


@dataclass(slots=True)
class HeroSkillData:
    name: str
    description: str


@dataclass(slots=True)
class HeroDetailData:
    slug: str
    name: str
    roles: list[str] = field(default_factory=list)
    lanes: list[str] = field(default_factory=list)
    specialties: list[str] = field(default_factory=list)
    skills: list[HeroSkillData] = field(default_factory=list)
    stats: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class RankingEntry:
    id: int | None
    name: str
    slug: str | None = None
    head_image: str | None = None
    win_rate: float = 0.0
    ban_rate: float = 0.0
    pick_rate: float = 0.0
    tier: str | None = None


@dataclass(slots=True)
class TrendPoint:
    date: str
    win_rate: float = 0.0
    ban_rate: float = 0.0
    pick_rate: float = 0.0


@dataclass(slots=True)
class PlayerProfileData:
    player_id: str
    zone_id: str
    ign: str
    avatar: str | None = None
    level: int | None = None
    rank_name: str | None = None
    rank_icon: str | None = None
    total_matches: int | None = None
    wins: int | None = None
    losses: int | None = None
    win_rate: float | None = None
    kda: float | None = None
    mvp_count: int | None = None
