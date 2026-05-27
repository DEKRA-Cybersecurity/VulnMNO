from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.models import AdminUser, AuditEvent, Customer, Purchase, Refund, SupportTicket

from ..deps import get_current_admin
from ..templates_loader import render

router = APIRouter(prefix="/admin")


@router.get("/")
async def dashboard(
    request: Request,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    customers = (await session.execute(select(func.count()).select_from(Customer))).scalar_one()
    purchases_7d = (await session.execute(
        select(func.count()).select_from(Purchase).where(Purchase.status == "confirmed")
    )).scalar_one()
    open_tickets = (await session.execute(
        select(func.count()).select_from(SupportTicket).where(SupportTicket.status == "open")
    )).scalar_one()
    pending_refunds = (await session.execute(
        select(func.count()).select_from(Refund).where(Refund.status == "pending")
    )).scalar_one()
    recent_audit = (await session.execute(
        select(AuditEvent).order_by(AuditEvent.id.desc()).limit(10)
    )).scalars().all()

    return render(
        request,
        "admin/dashboard.html",
        {
            "kpi": {
                "customers": customers,
                "purchases_confirmed": purchases_7d,
                "open_tickets": open_tickets,
                "pending_refunds": pending_refunds,
            },
            "recent_audit": recent_audit,
        },
    )
