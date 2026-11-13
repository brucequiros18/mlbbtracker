"""Shared response envelope.

Every endpoint answers with ``{"data": ..., "meta": ...}`` so clients have one
shape to parse. ``meta`` carries attribution and freshness information — the
upstream licenses (CC BY-SA wiki data) require crediting the source.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class ApiModel(BaseModel):
    """Base schema: emits camelCase JSON while keeping snake_case Python.

    The Dart client models expect camelCase (`winRate`, `headImage`), so the
    wire format is camelCase; `populate_by_name` lets the service layer keep
    constructing models with snake_case kwargs.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SourceInfo(ApiModel):
    name: str
    url: str
    license: str | None = None


class Meta(ApiModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cached: bool = False
    count: int | None = None
    note: str | None = None
    sources: list[SourceInfo] = Field(default_factory=list)


class ListResponse(ApiModel, Generic[T]):
    data: list[T]
    meta: Meta


class ItemResponse(ApiModel, Generic[T]):
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
