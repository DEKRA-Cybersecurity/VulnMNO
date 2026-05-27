from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.deps import get_current_customer, get_session
from app.errors import AppError, ErrorCode, bad_request, conflict, not_found
from app.ids import (
    next_attachment_id,
    next_message_id,
    next_ticket_id,
)
from app.models import Customer, SupportTicket, TicketAttachment, TicketMessage
from app.schemas.common import Page
from app.schemas.support import (
    CreateMessageRequest,
    CreateTicketRequest,
    TicketAttachmentRead,
    TicketAuthor,
    TicketMessageRead,
    TicketRead,
    TicketSummaryRead,
)
from app.services.audit import write_audit
from app.services.pagination import paginate

router = APIRouter(prefix="/api/support", tags=["support"])


def _summary(t: SupportTicket, customer: Customer) -> TicketSummaryRead:
    return TicketSummaryRead(
        ticketId=t.public_id,
        customerId=customer.public_id,
        topic=t.topic,
        status=t.status,
        createdAt=t.created_at,
        lastUpdatedAt=t.last_updated_at,
    )


def _msg(m: TicketMessage) -> TicketMessageRead:
    return TicketMessageRead(
        messageId=m.public_id,
        ticketId="",  # filled by caller
        author=TicketAuthor(role=m.author_role, displayName=m.author_display_name),
        body=m.body,
        createdAt=m.created_at,
    )


def _attachment(a: TicketAttachment) -> TicketAttachmentRead:
    return TicketAttachmentRead(
        attachmentId=a.public_id,
        ticketId="",
        filename=a.filename,
        sizeBytes=a.size_bytes,
        contentType=a.content_type,
        uploadedAt=a.created_at,
    )


async def _load_ticket_full(
    session: AsyncSession, customer: Customer, *, public_id: str
) -> SupportTicket | None:
    return (
        await session.execute(
            select(SupportTicket)
            .where(
                SupportTicket.public_id == public_id,
                SupportTicket.customer_id == customer.id,
            )
            .options(
                selectinload(SupportTicket.messages),
                selectinload(SupportTicket.attachments),
            )
        )
    ).scalar_one_or_none()


def _full(t: SupportTicket, customer: Customer) -> TicketRead:
    messages = [
        _msg(m).model_copy(update={"ticketId": t.public_id}) for m in t.messages
    ]
    attachments = [
        _attachment(a).model_copy(update={"ticketId": t.public_id}) for a in (t.attachments or [])
    ]
    return TicketRead(
        ticketId=t.public_id,
        customerId=customer.public_id,
        topic=t.topic,
        status=t.status,
        createdAt=t.created_at,
        lastUpdatedAt=t.last_updated_at,
        description=t.description,
        messages=messages,
        attachments=attachments,
    )


@router.post("/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: CreateTicketRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ticket = SupportTicket(
        public_id=await next_ticket_id(session),
        customer_id=customer.id,
        topic=body.topic,
        description=body.description,
        status="open",
    )
    session.add(ticket)
    await session.flush()
    msg = TicketMessage(
        public_id=await next_message_id(session),
        ticket_id=ticket.id,
        author_role="customer",
        author_display_name=customer.name,
        body=body.description,
    )
    session.add(msg)
    await session.flush()
    full = await _load_ticket_full(session, customer, public_id=ticket.public_id)
    assert full is not None
    await write_audit(
        session,
        event_type="SUPPORT_TICKET_CREATED",
        actor_id=customer.public_id,
        target_type="ticket",
        target_id=ticket.public_id,
        payload={"topic": body.topic},
    )
    return _full(full, customer)


@router.get("/tickets", response_model=Page[TicketSummaryRead])
async def list_tickets(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    status_q: str | None = Query(default=None, alias="status"),
):
    stmt = select(SupportTicket).where(
        SupportTicket.customer_id == customer.id, SupportTicket.deleted_at.is_(None)
    )
    if status_q:
        stmt = stmt.where(SupportTicket.status == status_q)
    rows, nxt = await paginate(
        session, stmt, id_column=SupportTicket.id, limit=limit, cursor=cursor
    )
    return Page(items=[_summary(t, customer) for t in rows], nextCursor=nxt)


@router.get("/tickets/{ticketId}", response_model=TicketRead)
async def get_ticket(
    ticketId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ticket = await _load_ticket_full(session, customer, public_id=ticketId)
    if ticket is None:
        raise not_found("Ticket not found")
    return _full(ticket, customer)


async def _load_open_ticket(
    session: AsyncSession, customer: Customer, ticket_id: str
) -> SupportTicket:
    ticket = (
        await session.execute(
            select(SupportTicket).where(
                SupportTicket.public_id == ticket_id, SupportTicket.customer_id == customer.id
            )
        )
    ).scalar_one_or_none()
    if ticket is None:
        raise not_found("Ticket not found")
    if ticket.status == "closed":
        raise conflict(ErrorCode.TICKET_CLOSED, "Ticket is closed")
    return ticket


@router.post(
    "/tickets/{ticketId}/messages",
    response_model=TicketMessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_message(
    ticketId: str,
    body: CreateMessageRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ticket = await _load_open_ticket(session, customer, ticketId)
    msg = TicketMessage(
        public_id=await next_message_id(session),
        ticket_id=ticket.id,
        author_role="customer",
        author_display_name=customer.name,
        body=body.body,
    )
    session.add(msg)
    await session.flush()
    return _msg(msg).model_copy(update={"ticketId": ticket.public_id})


@router.post(
    "/tickets/{ticketId}/attachments",
    response_model=TicketAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_attachment(
    ticketId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    file: UploadFile = File(...),
):
    settings = get_settings()
    ticket = await _load_open_ticket(session, customer, ticketId)

    contents = await file.read()
    if len(contents) > settings.attachment_max_bytes:
        raise bad_request(ErrorCode.VALIDATION_FAILED, "File too large")

    target_dir: Path = settings.uploads_dir / customer.public_id / ticket.public_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / (file.filename or "upload.bin")
    target.write_bytes(contents)

    att = TicketAttachment(
        public_id=await next_attachment_id(session),
        ticket_id=ticket.id,
        filename=file.filename or "upload.bin",
        size_bytes=len(contents),
        content_type=file.content_type or "application/octet-stream",
        storage_path=str(target),
    )
    session.add(att)
    await session.flush()
    return _attachment(att).model_copy(update={"ticketId": ticket.public_id})


@router.post("/tickets/{ticketId}/close", response_model=TicketRead)
async def close_ticket(
    ticketId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ticket = (
        await session.execute(
            select(SupportTicket).where(
                SupportTicket.public_id == ticketId, SupportTicket.customer_id == customer.id
            )
        )
    ).scalar_one_or_none()
    if ticket is None:
        raise not_found("Ticket not found")
    if ticket.status == "closed":
        raise conflict(ErrorCode.CONFLICT, "Ticket already closed")
    ticket.status = "closed"
    await session.flush()
    full = await _load_ticket_full(session, customer, public_id=ticket.public_id)
    assert full is not None
    return _full(full, customer)
