from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_session
from app.errors import AppError, ErrorCode, conflict, not_found
from app.ids import next_message_id
from app.models import AdminUser, Customer, SupportTicket, TicketMessage

from ..deps import require_csrf, require_module
from ..permissions import Access, Module
from ..services.audit import write_admin_audit
from ..templates_loader import render

router = APIRouter(prefix="/admin/tickets")


@router.get("")
async def tickets_list(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.TICKET_MANAGEMENT, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = None,
    topic: str | None = None,
):
    stmt = select(SupportTicket).where(SupportTicket.deleted_at.is_(None))
    if status_filter:
        stmt = stmt.where(SupportTicket.status == status_filter)
    if topic:
        stmt = stmt.where(SupportTicket.topic == topic)
    tickets = (
        await session.execute(stmt.order_by(SupportTicket.id.desc()).limit(50))
    ).scalars().all()
    return render(request, "admin/tickets/list.html",
                  {"tickets": tickets, "status_filter": status_filter, "topic_filter": topic})


@router.get("/{ticketId}")
async def ticket_detail(
    request: Request,
    ticketId: str,
    admin: Annotated[AdminUser, Depends(require_module(Module.TICKET_MANAGEMENT, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ticket = (
        await session.execute(
            select(SupportTicket)
            .where(SupportTicket.public_id == ticketId)
            .options(selectinload(SupportTicket.messages), selectinload(SupportTicket.attachments))
        )
    ).scalar_one_or_none()
    if ticket is None:
        raise not_found("Ticket not found")
    customer = (
        await session.execute(select(Customer).where(Customer.id == ticket.customer_id))
    ).scalar_one()
    can_write = admin.role in ("support_agent", "ops_admin")
    return render(request, "admin/tickets/detail.html",
                  {"ticket": ticket, "customer": customer, "can_write": can_write})


@router.post("/{ticketId}/agent-reply")
async def agent_reply(
    request: Request,
    ticketId: str,
    body: Annotated[str, Form()],
    admin: Annotated[AdminUser, Depends(require_module(Module.TICKET_MANAGEMENT, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    if not body.strip():
        raise AppError(ErrorCode.VALIDATION_FAILED, "Reply body is empty", http_status=400)
    ticket = (
        await session.execute(select(SupportTicket).where(SupportTicket.public_id == ticketId))
    ).scalar_one_or_none()
    if ticket is None:
        raise not_found("Ticket not found")
    if ticket.status == "closed":
        raise conflict(ErrorCode.TICKET_CLOSED, "Ticket is closed")
    session.add(TicketMessage(
        public_id=await next_message_id(session),
        ticket_id=ticket.id,
        author_role="agent",
        author_display_name=admin.full_name,
        body=body,
    ))
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_TICKET_REPLY",
        target_type="ticket", target_id=ticketId, request=request,
    )
    return RedirectResponse(url=f"/admin/tickets/{ticketId}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{ticketId}/close")
async def ticket_close(
    request: Request,
    ticketId: str,
    admin: Annotated[AdminUser, Depends(require_module(Module.TICKET_MANAGEMENT, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    ticket = (
        await session.execute(select(SupportTicket).where(SupportTicket.public_id == ticketId))
    ).scalar_one_or_none()
    if ticket is None:
        raise not_found("Ticket not found")
    if ticket.status == "closed":
        raise conflict(ErrorCode.CONFLICT, "Ticket already closed")
    ticket.status = "closed"
    await write_admin_audit(
        session, admin=admin, event_type="ADMIN_TICKET_CLOSED",
        target_type="ticket", target_id=ticketId, request=request,
    )
    return RedirectResponse(url=f"/admin/tickets/{ticketId}", status_code=status.HTTP_303_SEE_OTHER)
