from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.models import AdminUser, AuditEvent

from ..deps import require_module
from ..permissions import Access, Module
from ..templates_loader import render

router = APIRouter(prefix="/admin/audit")


@router.get("")
async def audit_list(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.AUDIT_LOG, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
    event_type: str | None = None,
    actor_id: str | None = None,
    from_: str | None = None,
    to: str | None = None,
    limit: int = 50,
):
    stmt = select(AuditEvent)
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    if actor_id:
        stmt = stmt.where(AuditEvent.actor_id == actor_id)
    if from_:
        try:
            stmt = stmt.where(AuditEvent.timestamp >= datetime.fromisoformat(from_))
        except ValueError:
            pass
    if to:
        try:
            stmt = stmt.where(AuditEvent.timestamp <= datetime.fromisoformat(to))
        except ValueError:
            pass
    stmt = stmt.order_by(AuditEvent.id.desc()).limit(max(1, min(limit, 200)))
    events = (await session.execute(stmt)).scalars().all()
    return render(request, "admin/audit/list.html",
                  {"events": events, "filters": {
                      "event_type": event_type or "",
                      "actor_id": actor_id or "",
                      "from": from_ or "",
                      "to": to or "",
                  }})
