"""Shared response envelope.

Every endpoint answers with ``{"data": ..., "meta": ...}`` so clients have one
shape to parse. ``meta`` carries attribution and freshness information — the
upstream licenses (CC BY-SA wiki data) require crediting the source.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SourceInfo(BaseModel):
    name: str
    url: str
    license: str | None = None


class Meta(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cached: bool = False
    count: int | None = None
    note: str | None = None
    sources: list[SourceInfo] = Field(default_factory=list)


class ListResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: Meta


class ItemResponse(BaseModel, Generic[T]):
    data: T
    meta: Meta


RONE_SOURCE = SourceInfo(
    name="Rone Arena API",
    url="https://arena.rone.dev/",
    license="Unofficial community API; game data from Moonton public services",
)
DEX_SOURCE = SourceInfo(
    name="MLBBDex",
    url="https://mlbbdex.com/",
    license="CC BY-SA (Mobile Legends wiki) + MIT (written analysis)",
)
