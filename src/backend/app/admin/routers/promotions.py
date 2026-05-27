from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.errors import AppError, ErrorCode, not_found
from app.models import AdminUser, Coupon, Promotion

from ..deps import require_csrf, require_module
from ..permissions import Access, Module
from ..services.audit import write_admin_audit
from ..templates_loader import render

router = APIRouter(prefix="/admin/promotions")


@router.get("")
async def promo_list(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.PROMOTION_CATALOG, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    promos = (await session.execute(select(Promotion).order_by(Promotion.public_id))).scalars().all()
    can_edit = admin.role in ("product_manager", "ops_admin")
    return render(request, "admin/promotions/list.html", {"promos": promos, "can_edit": can_edit})


@router.post("/new")
async def promo_new(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.PROMOTION_CATALOG, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
    public_id: Annotated[str, Form()],
    name: Annotated[str, Form()],
    discount_type: Annotated[str, Form()],
    discount_value: Annotated[str, Form()],
    starts_at: Annotated[str, Form()],
    ends_at: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
):
    if (await session.execute(select(Promotion).where(Promotion.public_id == public_id))).scalar_one_or_none():
        raise AppError(ErrorCode.CONFLICT, "Promotion exists", http_status=409)
    promo = Promotion(
        public_id=public_id,
        name=name,
        description=description,
        discount_type=discount_type,
        discount_value=Decimal(discount_value),
        starts_at=datetime.fromisoformat(starts_at).replace(tzinfo=timezone.utc),
        ends_at=datetime.fromisoformat(ends_at).replace(tzinfo=timezone.utc),
    )
    session.add(promo)
    await session.flush()
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_PROMOTION_CREATED",
        target_type="promotion", target_id=public_id, request=request,
    )
    return RedirectResponse(url="/admin/promotions", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{promoId}/coupons/generate")
async def coupons_generate(
    request: Request,
    promoId: str,
    admin: Annotated[AdminUser, Depends(require_module(Module.COUPON_CATALOG, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
    count: Annotated[int, Form()] = 10,
):
    if not 1 <= count <= 1000:
        raise AppError(ErrorCode.VALIDATION_FAILED, "count must be 1..1000", http_status=400)
    promo = (await session.execute(select(Promotion).where(Promotion.public_id == promoId))).scalar_one_or_none()
    if promo is None:
        raise not_found("Promotion not found")
    alphabet = string.ascii_uppercase + string.digits
    created = []
    for _i in range(count):
        code = "".join(secrets.choice(alphabet) for _ in range(10))
        session.add(Coupon(code=code, promotion_id=promo.id, usage_limit=1))
        created.append(code)
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_COUPONS_GENERATED",
        target_type="promotion", target_id=promoId,
        payload={"count": count}, request=request,
    )
    return RedirectResponse(url="/admin/promotions", status_code=status.HTTP_303_SEE_OTHER)
