from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.errors import AppError, ErrorCode, not_found
from app.models import AdminUser

from ..deps import require_csrf, require_module
from ..permissions import Access, Module
from ..security import hash_admin_password
from ..services.audit import write_admin_audit
from ..templates_loader import render

router = APIRouter(prefix="/admin/staff")


@router.get("")
async def staff_list(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.ADMIN_USERS_MANAGEMENT, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    rows = (await session.execute(
        select(AdminUser).where(AdminUser.deleted_at.is_(None)).order_by(AdminUser.public_id)
    )).scalars().all()
    return render(request, "admin/staff/list.html", {"rows": rows})


@router.post("/new")
async def staff_new(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.ADMIN_USERS_MANAGEMENT, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    role: Annotated[str, Form()],
    full_name: Annotated[str, Form()],
):
    if (await session.execute(select(AdminUser).where(AdminUser.username == username))).scalar_one_or_none():
        raise AppError(ErrorCode.CONFLICT, "Username already exists", http_status=409)
    if role not in (
        "support_agent", "billing_operator", "product_manager",
        "ops_admin", "security_analyst", "supplier_admin",
    ):
        raise AppError(ErrorCode.VALIDATION_FAILED, "Invalid role", http_status=400)
    if len(password) < 8:
        raise AppError(ErrorCode.VALIDATION_FAILED, "Password must be ≥ 8 chars", http_status=400)
    n = (await session.execute(select(AdminUser))).scalars().all()
    new_id = 10000 + len(n) + 1
    user = AdminUser(
        public_id=f"ADM-{new_id}",
        username=username,
        password_hash=hash_admin_password(password),
        role=role,
        full_name=full_name,
        status="active",
    )
    session.add(user)
    await session.flush()
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_STAFF_CREATED",
        target_type="admin_user", target_id=user.public_id,
        payload={"role": role, "username": username}, request=request,
    )
    return RedirectResponse(url="/admin/staff", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{adminId}/deactivate")
async def staff_deactivate(
    request: Request,
    adminId: str,
    admin: Annotated[AdminUser, Depends(require_module(Module.ADMIN_USERS_MANAGEMENT, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    target = (await session.execute(select(AdminUser).where(AdminUser.public_id == adminId))).scalar_one_or_none()
    if target is None:
        raise not_found("Admin user not found")
    if target.id == admin.id:
        raise AppError(ErrorCode.CONFLICT, "Cannot deactivate yourself", http_status=409)
    target.status = "deactivated"
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_STAFF_DEACTIVATED",
        target_type="admin_user", target_id=adminId, request=request,
    )
    return RedirectResponse(url="/admin/staff", status_code=status.HTTP_303_SEE_OTHER)
