from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.models import AdminUser, AuditEvent, Customer, Purchase, Refund, SupportTicket

from ..deps import require_module
from ..permissions import Access, Module
from ..templates_loader import render

router = APIRouter(prefix="/admin/reports")


@router.get("")
async def reports(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.REPORTING, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    last_7d = datetime.now(timezone.utc) - timedelta(days=7)

    customers = (await session.execute(select(func.count()).select_from(Customer))).scalar_one()
    purchases_7d = (await session.execute(
        select(func.count()).select_from(Purchase)
        .where(Purchase.created_at >= last_7d, Purchase.status == "confirmed")
    )).scalar_one()
    refund_total = (await session.execute(
        select(func.count()).select_from(Refund)
    )).scalar_one() or 1
    refund_approved = (await session.execute(
        select(func.count()).select_from(Refund).where(Refund.status == "approved")
    )).scalar_one()
    refund_rate = round(100.0 * refund_approved / refund_total, 1)
    tickets_open = (await session.execute(
        select(func.count()).select_from(SupportTicket).where(SupportTicket.status == "open")
    )).scalar_one()
    rate_limit_hits_24h = (await session.execute(
        select(func.count()).select_from(AuditEvent)
        .where(AuditEvent.timestamp >= last_24h, AuditEvent.event_type == "RATE_LIMIT_HIT")
    )).scalar_one()

    return render(
        request,
        "admin/reports.html",
        {
            "kpi": {
                "customers": customers,
                "purchases_confirmed_7d": purchases_7d,
                "refund_approval_rate_pct": refund_rate,
                "tickets_open": tickets_open,
                "rate_limit_hits_24h": rate_limit_hits_24h,
            },
        },
    )
