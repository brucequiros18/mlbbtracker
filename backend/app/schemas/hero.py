"""Hero API schemas."""

from __future__ import annotations

from pydantic import Field

from app.integrations.models import HeroDetailData, HeroRef, RankingEntry
from app.schemas.common import ApiModel


class HeroSummary(ApiModel):
    id: int
    name: str
    slug: str
    roles: list[str] = Field(default_factory=list)
    lanes: list[str] = Field(default_factory=list)
    head_image: str | None = None
    tier: str | None = None


class HeroSkill(ApiModel):
    name: str
    description: str


class HeroRankStat(ApiModel):
    win_rate: float
    ban_rate: float
    pick_rate: float


class HeroDetail(ApiModel):
    id: int | None
    name: str
    slug: str
    roles: list[str] = Field(default_factory=list)
    lanes: list[str] = Field(default_factory=list)
    specialties: list[str] = Field(default_factory=list)
    head_image: str | None = None
    portrait: str | None = None
    skills: list[HeroSkill] = Field(default_factory=list)
    strong_against: list[str] = Field(default_factory=list)
    weak_against: list[str] = Field(default_factory=list)
    rank_stat: HeroRankStat | None = None


class HeroTrendPoint(ApiModel):
    date: str
    win_rate: float
    ban_rate: float
    pick_rate: float


class HeroHistoryPoint(ApiModel):
    """One recorded daily snapshot (our own observations, not provider data)."""

    captured_on: str
    win_rate: float
    ban_rate: float
    pick_rate: float
    tier: str | None = None
    rank_position: int | None = None


class HeroRanking(ApiModel):
    id: int
    name: str
    slug: str | None = None
    head_image: str | None = None
    win_rate: float
    ban_rate: float
    pick_rate: float
    tier: str | None = None

    @classmethod
    def from_entry(cls, entry: RankingEntry, *, slug: str | None, tier: str | None) -> "HeroRanking":
        return cls(
            id=entry.id or 0,
            name=entry.name,
            slug=entry.slug or slug,
            head_image=entry.head_image,
            win_rate=round(entry.win_rate, 6),
            ban_rate=round(entry.ban_rate, 6),
            pick_rate=round(entry.pick_rate, 6),
            tier=entry.tier or tier,
        )


def summary_from_ref(ref: HeroRef, *, slug: str, roles: list[str], lanes: list[str], tier: str | None) -> HeroSummary:
    return HeroSummary(
        id=ref.id,
        name=ref.name,
        slug=slug,
        roles=roles,
        lanes=lanes,
        head_image=ref.head_image,
        tier=tier,
    )


def detail_from_data(
    data: HeroDetailData,
    *,
    hero_id: int | None,
    head_image: str | None,
    strong_against: list[str],
    weak_against: list[str],
    rank_stat: HeroRankStat | None,
) -> HeroDetail:
    return HeroDetail(
        id=hero_id,
        name=data.name,
        slug=data.slug,
        roles=data.roles,
        lanes=data.lanes,
        specialties=data.specialties,
        head_image=head_image,
        portrait=head_image,
        skills=[HeroSkill(name=s.name, description=s.description) for s in data.skills],
        strong_against=strong_against,
        weak_against=weak_against,
        rank_stat=rank_stat,
    )
