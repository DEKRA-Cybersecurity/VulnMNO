from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.models import AdminUser
from app.security import now

from ..deps import require_csrf
from ..security import (
    clear_admin_session,
    current_session_admin,
    set_admin_session,
    verify_admin_password,
)
from ..services.audit import write_admin_audit
from ..templates_loader import render

router = APIRouter(prefix="/admin")


@router.get("/login")
async def login_form(request: Request, next: str = "/admin/"):
    # If already logged in, send to dashboard.
    if current_session_admin(request) is not None:
        return RedirectResponse(url=next or "/admin/", status_code=status.HTTP_303_SEE_OTHER)
    # Issue a CSRF token bound to the (currently anonymous) session.
    csrf = set_admin_session.__wrapped__ if False else None  # no-op, kept for symmetry
    import secrets

    request.session["csrf"] = secrets.token_urlsafe(32)
    return render(request, "admin/login.html", {"next": next, "error": None})


from app.rate_limit import limiter  # noqa: E402


@router.post("/login")
@limiter.limit("5/minute")
async def login_submit(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    csrf_token: Annotated[str, Form()],
    next: Annotated[str, Form()] = "/admin/",
):
    # Validate the pre-issued CSRF token against the anonymous session.
    expected_csrf = request.session.get("csrf")
    import secrets

    if not expected_csrf or not secrets.compare_digest(expected_csrf, csrf_token):
        return render(
            request,
            "admin/login.html",
            {"next": next, "error": "Session expired. Please reload and try again."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    admin = (
        await session.execute(select(AdminUser).where(AdminUser.username == username))
    ).scalar_one_or_none()

    if (
        admin is None
        or admin.deleted_at is not None
        or admin.status != "active"
        or not verify_admin_password(password, admin.password_hash)
    ):
        # Audit failure (no actor_id since we don't know the role); attempted username goes in payload.
        from app.services.audit import write_audit

        await write_audit(
            session,
            event_type="ADMIN_LOGIN_FAILED",
            actor_id=None,
            target_type="admin_username",
            target_id=username,
            ip_address=request.client.host if request.client else None,
        )
        return render(
            request,
            "admin/login.html",
            {"next": next, "error": "Invalid credentials."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    admin.last_login_at = now()
    set_admin_session(
        request,
        admin_id=admin.id,
        admin_public_id=admin.public_id,
        role=admin.role,
    )
    await write_admin_audit(
        session,
        admin=admin,
        event_type="ADMIN_LOGIN_SUCCESS",
        request=request,
    )

    # Sanitize the `next` URL — only allow paths under /admin/.
    target = next if next.startswith("/admin/") else "/admin/"
    return RedirectResponse(url=target, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
async def logout(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    sess = current_session_admin(request)
    if sess is not None:
        admin = (
            await session.execute(select(AdminUser).where(AdminUser.id == sess["id"]))
        ).scalar_one_or_none()
        if admin is not None:
            await write_admin_audit(session, admin=admin, event_type="ADMIN_LOGOUT", request=request)
    clear_admin_session(request)
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
