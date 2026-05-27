from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Customer,
    Invoice,
    Notification,
    PlanChange,
    Purchase,
    Refund,
    SIMProfile,
    SupportTicket,
    TicketAttachment,
    TicketMessage,
    Transaction,
    UsageRecord,
)


async def _next_int(session: AsyncSession, model: type, column: str, base: int) -> int:
    """Return next integer suffix for a public_id column, starting from `base`."""
    stmt = select(func.count()).select_from(model)
    n = (await session.execute(stmt)).scalar_one()
    return base + int(n) + 1


async def next_customer_id(session: AsyncSession) -> str:
    return f"CUST-{await _next_int(session, Customer, 'public_id', 10000)}"


async def next_purchase_id(session: AsyncSession) -> str:
    return f"PUR-{await _next_int(session, Purchase, 'public_id', 90000)}"


async def next_transaction_id(session: AsyncSession) -> str:
    return f"TX-{await _next_int(session, Transaction, 'public_id', 50000)}"


async def next_invoice_id(session: AsyncSession) -> str:
    return f"INV-{await _next_int(session, Invoice, 'public_id', 20000)}"


async def next_usage_id(session: AsyncSession) -> str:
    return f"USG-{await _next_int(session, UsageRecord, 'public_id', 70000)}"


async def next_ticket_id(session: AsyncSession) -> str:
    return f"TCK-{await _next_int(session, SupportTicket, 'public_id', 30000)}"


async def next_message_id(session: AsyncSession) -> str:
    return f"MSG-{await _next_int(session, TicketMessage, 'public_id', 40000)}"


async def next_attachment_id(session: AsyncSession) -> str:
    return f"ATT-{await _next_int(session, TicketAttachment, 'public_id', 60000)}"


async def next_notification_id(session: AsyncSession) -> str:
    return f"NTF-{await _next_int(session, Notification, 'public_id', 50000)}"


async def next_plan_change_id(session: AsyncSession) -> str:
    return f"PCH-{await _next_int(session, PlanChange, 'public_id', 10000)}"


async def next_refund_id(session: AsyncSession) -> str:
    return f"REF-{await _next_int(session, Refund, 'public_id', 10000)}"


async def next_sim_id(session: AsyncSession) -> str:
    return f"SIM-{await _next_int(session, SIMProfile, 'public_id', 80000)}"
