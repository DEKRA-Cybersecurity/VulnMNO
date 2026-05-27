from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.errors import AppError, ErrorCode, not_found
from app.models import AdminUser, Plan

from ..deps import require_csrf, require_module
from ..permissions import Access, Module
from ..services.audit import write_admin_audit
from ..templates_loader import render

router = APIRouter(prefix="/admin/plans")


@router.get("")
async def plans_list(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.PLAN_CATALOG, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    plans = (await session.execute(select(Plan).order_by(Plan.public_id))).scalars().all()
    can_edit = admin.role in ("product_manager", "ops_admin")
    return render(request, "admin/plans/list.html", {"plans": plans, "can_edit": can_edit})


@router.post("/new")
async def plans_new(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.PLAN_CATALOG, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
    public_id: Annotated[str, Form()],
    name: Annotated[str, Form()],
    monthly_price: Annotated[str, Form()],
    data_limit_mb: Annotated[int, Form()] = 0,
    voice_limit_min: Annotated[int, Form()] = 0,
    sms_limit: Annotated[int, Form()] = 0,
    category: Annotated[str, Form()] = "prepaid",
    description: Annotated[str, Form()] = "",
):
    if (await session.execute(select(Plan).where(Plan.public_id == public_id))).scalar_one_or_none():
        raise AppError(ErrorCode.CONFLICT, "Plan with this public_id already exists", http_status=409)
    plan = Plan(
        public_id=public_id,
        name=name,
        description=description,
        monthly_price=Decimal(monthly_price),
        data_limit_mb=data_limit_mb,
        voice_limit_min=voice_limit_min,
        sms_limit=sms_limit,
        category=category,
    )
    session.add(plan)
    await session.flush()
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_PLAN_CREATED",
        target_type="plan", target_id=public_id, request=request,
    )
    return RedirectResponse(url="/admin/plans", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{planId}/archive")
async def plans_archive(
    request: Request,
    planId: str,
    admin: Annotated[AdminUser, Depends(require_module(Module.PLAN_CATALOG, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    plan = (await session.execute(select(Plan).where(Plan.public_id == planId))).scalar_one_or_none()
    if plan is None:
        raise not_found("Plan not found")
    # Plan has no status column in Phase 1; we use eligibility_rules JSON to mark archived.
    rules = dict(plan.eligibility_rules or {})
    rules["archived"] = True
    plan.eligibility_rules = rules
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_PLAN_ARCHIVED",
        target_type="plan", target_id=planId, request=request,
    )
    return RedirectResponse(url="/admin/plans", status_code=status.HTTP_303_SEE_OTHER)
