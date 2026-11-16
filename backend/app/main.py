"""FastAPI application entry point.

Run locally::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.health_log import set_health_sink
from app.core.logging import configure_logging, get_logger
from app.db.base import get_session_factory
from app.db.repo import record_provider_health
from app.integrations.provider_factory import get_providers
from app.services.release_service import apk_path, read_manifest, render_download_page

logger = get_logger(__name__)


def _health_sink(**kwargs) -> None:
    """Persist provider call outcomes (used by the health log)."""
    record_provider_health(get_session_factory(), **kwargs)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Baseline hardening headers for the browser-facing deployment."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        if request.url.path.startswith((settings_api_prefix(), "/api")):
            response.headers.setdefault("Cache-Control", "no-store")
        return response


def settings_api_prefix() -> str:
    return get_settings().api_v1_prefix


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    logger.info("starting %s v%s (%s)", settings.app_name, __version__, settings.environment)
    set_health_sink(_health_sink)
    yield
    set_health_sink(None)
    await get_providers().aclose()
    logger.info("shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Backend for MLBB Tracker. Aggregates Mobile Legends: Bang Bang hero, meta "
            "and esports data from community providers behind a normalized REST API, and "
            "serves a player's own statistics through a consented sign-in (a one-time "
            "code, never a password). The app never displays fabricated data."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": str(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/api/meta", tags=["meta"], summary="API index")
    async def meta() -> dict:
        return {
            "name": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "openapi": "/openapi.json",
            "api": settings.api_v1_prefix,
        }

    # — Download page (registered before the `/` web mount so it wins) ————
    # Plain server-rendered HTML: indexable and functional without JS.
    # A missing release renders an honest "not published yet" state.
    @app.api_route("/download", methods=["GET", "HEAD"], include_in_schema=False)
    async def download_page() -> HTMLResponse:
        manifest = read_manifest(settings.resolved_releases_dir())
        return HTMLResponse(
            render_download_page(manifest),
            headers={
                "Cache-Control": "no-store",
                "Content-Security-Policy": (
                    "default-src 'none'; style-src 'unsafe-inline'; "
                    "img-src data:; base-uri 'none'; form-action 'none'; "
                    "frame-ancestors 'none'"
                ),
            },
        )

    @app.api_route(
        "/downloads/{filename}", methods=["GET", "HEAD"], include_in_schema=False
    )
    async def download_release_file(filename: str) -> FileResponse:
        path = apk_path(settings.resolved_releases_dir(), filename)
        if path is None:
            raise HTTPException(status_code=404, detail="No such release file.")
        return FileResponse(
            path,
            media_type="application/vnd.android.package-archive",
            filename=filename,
        )

    # Serve the Flutter web build from the same origin when one is present.
    # Same-origin means no CORS setup and a single deployable unit.
    web_root = settings.resolved_web_root()
    if web_root is not None:
        app.mount("/", StaticFiles(directory=str(web_root), html=True), name="web")
        logger.info("serving web app from %s", web_root)
    else:
        @app.get("/", tags=["meta"], summary="API index")
        async def index() -> dict:
            return {
                "name": settings.app_name,
                "version": __version__,
                "docs": "/docs",
                "openapi": "/openapi.json",
                "api": settings.api_v1_prefix,
                "web": "not built — run `flutter build web --release` in mobile/",
            }

    return app


app = create_app()
