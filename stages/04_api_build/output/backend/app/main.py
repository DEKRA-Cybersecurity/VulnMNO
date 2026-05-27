from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.admin.deps import AdminRedirectToLogin
from app.admin.routers import admin_router
from app.config import get_settings
from app.db import engine
from app.errors import AppError, ErrorCode
from app.i18n import parse_locale, translate
from app.models import Base
from app.rate_limit import limiter
from app.routers import (
    accounts,
    auth,
    customers,
    loyalty,
    notifications,
    plans,
    shop,
    support,
    usage,
)

log = logging.getLogger("vulnmno")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = BACKEND_ROOT / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if settings.seed_on_startup:
        from app.seed import run_seed

        try:
            await run_seed()
        except Exception as exc:
            log.warning("seed skipped: %s", exc)
    if settings.seed_phase2_on_startup:
        from app.seed_phase2 import run_seed as run_seed_phase2

        try:
            await run_seed_phase2()
        except Exception as exc:
            log.warning("seed_phase2 skipped: %s", exc)

    # Phase 2 — campaign scheduler background task.
    stop = asyncio.Event()
    from app.services.campaign_scheduler import run_forever

    scheduler_task = asyncio.create_task(run_forever(stop))

    try:
        yield
    finally:
        stop.set()
        scheduler_task.cancel()
        try:
            await scheduler_task
        except (asyncio.CancelledError, Exception):
            pass
        await engine.dispose()


def _wants_html(request: Request) -> bool:
    if request.url.path.startswith("/admin"):
        return True
    accept = request.headers.get("accept", "")
    return "text/html" in accept and "application/json" not in accept


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="VulnMNO API",
        version="0.2.0-phase2",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.admin_session_secret,
        session_cookie="vulnmno_admin_session",
        max_age=settings.admin_session_max_age_seconds,
        same_site="lax",
        https_only=settings.env != "dev",
    )

    # Phase 2 — rate limiting via slowapi.
    if settings.rate_limit_enabled:
        app.state.limiter = limiter
        app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        locale = parse_locale(request.headers.get("accept-language"))
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": ErrorCode.RATE_LIMITED.value,
                    "message": translate(locale, "error.rate_limited"),
                    "details": {"retryAfterSeconds": 60},
                }
            },
            headers={"Retry-After": "60"},
        )

    # Static files for admin (Bootstrap is loaded from CDN; this serves our admin.css/admin.js).
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.exception_handler(AdminRedirectToLogin)
    async def admin_redirect_handler(request: Request, exc: AdminRedirectToLogin):
        return RedirectResponse(
            url=f"/admin/login?next={exc.next_path}",
            status_code=303,
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        # Admin paths render HTML errors when possible; everything else stays JSON.
        if request.url.path.startswith("/admin") and _wants_html(request):
            body = (
                f"<!doctype html><meta charset='utf-8'>"
                f"<title>Error · VulnMNO admin</title>"
                f"<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css'>"
                f"<div class='container py-4'>"
                f"<h1 class='h4'>{exc.code.value}</h1>"
                f"<p>{exc.message}</p>"
                f"<a href='/admin/' class='btn btn-secondary btn-sm'>Back to dashboard</a>"
                f"</div>"
            )
            return HTMLResponse(content=body, status_code=exc.http_status)
        # JSON path — localize the message via Accept-Language when a translation exists.
        locale = parse_locale(request.headers.get("accept-language"))
        envelope = exc.envelope()
        key = f"error.{exc.code.value.lower()}"
        translated = translate(locale, key)
        if translated != key:  # only override if we actually have a translation
            envelope["error"]["message"] = translated
        return JSONResponse(status_code=exc.http_status, content=envelope)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        body = {
            "error": {
                "code": ErrorCode.VALIDATION_FAILED.value,
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            }
        }
        return JSONResponse(status_code=400, content=body)

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception):
        log.exception("unhandled: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {"code": ErrorCode.INTERNAL.value, "message": "Internal server error"}
            },
        )

    # Phase 1 routers (JSON API)
    app.include_router(auth.router)
    app.include_router(customers.router)
    app.include_router(accounts.router)
    app.include_router(shop.router)
    app.include_router(plans.router)
    app.include_router(usage.router)
    app.include_router(support.router)
    app.include_router(notifications.router)

    # Phase 2 — loyalty (JSON API)
    app.include_router(loyalty.router)

    # Phase 2 — admin portal (HTML)
    app.include_router(admin_router)

    return app


app = create_app()
