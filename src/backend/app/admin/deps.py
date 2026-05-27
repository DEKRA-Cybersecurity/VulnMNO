"""FastAPI dependencies for the admin portal."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.errors import AppError, ErrorCode
from app.models import AdminUser

from .permissions import Access, Module, Role, has_access
from .security import current_session_admin, verify_csrf


class AdminRedirectToLogin(HTTPException):
    """Raised when an /admin/* request lacks a valid session — handler redirects."""

    def __init__(self, next_path: str) -> None:
        super().__init__(status_code=status.HTTP_303_SEE_OTHER, detail={"next": next_path})
        self.next_path = next_path


async def get_current_admin(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AdminUser:
    sess = current_session_admin(request)
    if sess is None:
        # Preserve where the user was trying to go.
        raise AdminRedirectToLogin(next_path=request.url.path)
    admin = (
        await session.execute(select(AdminUser).where(AdminUser.id == sess["id"]))
    ).scalar_one_or_none()
    if admin is None or admin.deleted_at is not None or admin.status != "active":
        raise AdminRedirectToLogin(next_path=request.url.path)
    return admin


def require_module(module: Module, required: Access = Access.READ):
    """Dependency factory: enforces RBAC on a route."""

    async def _checker(admin: Annotated[AdminUser, Depends(get_current_admin)]) -> AdminUser:
        if not has_access(Role(admin.role), module, required):
            raise AppError(
                ErrorCode.ADMIN_FORBIDDEN,
                f"Role '{admin.role}' lacks {required.value} on '{module.value}'",
                http_status=403,
                details={"module": module.value, "required": required.value},
            )
        return admin

    return _checker


CsrfToken = Annotated[str | None, Form(alias="csrf_token")]


async def require_csrf(request: Request, csrf_token: CsrfToken = None) -> None:
    if not verify_csrf(request, csrf_token):
        raise AppError(
            ErrorCode.ADMIN_FORBIDDEN,
            "CSRF token missing or invalid",
            http_status=403,
            details={"reason": "csrf"},
        )
