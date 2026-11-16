"""Published app-release manifest (used by the download page and clients)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.schemas.common import ItemResponse, Meta
from app.services.release_service import read_manifest

router = APIRouter(tags=["app"])


@router.get(
    "/app/release",
    response_model=ItemResponse,
    summary="Latest published app release (version, size, SHA-256)",
)
async def app_release() -> ItemResponse:
    """The manifest behind the `/download` page.

    404 with `NOT_FOUND` until a release is packaged — a missing build is
    never fabricated.
    """
    manifest = read_manifest(get_settings().resolved_releases_dir())
    if manifest is None:
        raise NotFoundError("No app release has been published yet.")
    return ItemResponse(data=manifest, meta=Meta(sources=[]))
