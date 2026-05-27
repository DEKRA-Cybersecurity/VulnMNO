from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import IdempotencyKey, get_current_customer, get_session
from app.errors import AppError, ErrorCode, bad_request, not_found
from app.ids import next_invoice_id, next_refund_id, next_ticket_id, next_transaction_id
from app.models import (
    Account,
    Balance,
    Customer,
    Invoice,
    Purchase,
    Refund,
    SupportTicket,
    TicketMessage,
    Transaction,
)
from app.schemas.account import (
    BalanceRead,
    InvoiceLineItem as InvoiceLineItemSchema,
    InvoiceRead,
    InvoiceSummaryRead,
    RefundCreated,
    RefundRequest,
    TopupRequest,
    TransactionRead,
)
from app.schemas.common import Page
from app.services.audit import write_audit
from app.services.pagination import paginate

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


async def _customer_account(session: AsyncSession, customer: Customer) -> Account:
    acct = (
        await session.execute(select(Account).where(Account.customer_id == customer.id))
    ).scalar_one_or_none()
    if acct is None:
        raise not_found("Account not found")
    return acct


@router.get("/me/balance", response_model=BalanceRead)
async def get_balance(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    acct = await _customer_account(session, customer)
    bal = (await session.execute(select(Balance).where(Balance.account_id == acct.id))).scalar_one()
    return BalanceRead(
        accountId=acct.public_id,
        balance=bal.amount,
        currency=bal.currency,
        lastUpdated=bal.last_updated,
    )


@router.get("/me/transactions", response_model=Page[TransactionRead])
async def list_transactions(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    acct = await _customer_account(session, customer)
    rows, nxt = await paginate(
        session,
        select(Transaction).where(Transaction.account_id == acct.id),
        id_column=Transaction.id,
        limit=limit,
        cursor=cursor,
    )
    items = [_tx_read(t, acct.public_id) for t in rows]
    return Page(items=items, nextCursor=nxt)


def _tx_read(t: Transaction, account_public_id: str) -> TransactionRead:
    return TransactionRead(
        transactionId=t.public_id,
        accountId=account_public_id,
        type=t.type,
        amount=t.amount,
        currency=t.currency,
        balanceAfter=t.balance_after,
        timestamp=t.timestamp,
    )


@router.post(
    "/me/topup", response_model=TransactionRead, status_code=status.HTTP_201_CREATED
)
async def topup(
    body: TopupRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: IdempotencyKey = None,
):
    acct = await _customer_account(session, customer)
    bal = (await session.execute(select(Balance).where(Balance.account_id == acct.id))).scalar_one()
    bal.amount = (bal.amount or Decimal("0.00")) + Decimal(body.amount)

    tx = Transaction(
        public_id=await next_transaction_id(session),
        account_id=acct.id,
        type="topup",
        amount=Decimal(body.amount),
        currency=body.currency,
        balance_after=bal.amount,
    )
    session.add(tx)
    await session.flush()
    await write_audit(
        session,
        event_type="TOPUP",
        actor_id=customer.public_id,
        target_type="account",
        target_id=acct.public_id,
        payload={"amount": str(body.amount)},
    )
    return _tx_read(tx, acct.public_id)


@router.get("/me/invoices", response_model=Page[InvoiceSummaryRead])
async def list_invoices(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    acct = await _customer_account(session, customer)
    rows, nxt = await paginate(
        session,
        select(Invoice).where(Invoice.account_id == acct.id),
        id_column=Invoice.id,
        limit=limit,
        cursor=cursor,
    )
    items = [
        InvoiceSummaryRead(
            invoiceId=i.public_id,
            accountId=acct.public_id,
            period=i.period,
            totalAmount=i.total_amount,
            currency=i.currency,
            status=i.status,
            issuedAt=i.issued_at,
        )
        for i in rows
    ]
    return Page(items=items, nextCursor=nxt)


@router.get("/me/invoices/{invoiceId}", response_model=InvoiceRead)
async def get_invoice(
    invoiceId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    acct = await _customer_account(session, customer)
    inv = (
        await session.execute(
            select(Invoice)
            .where(Invoice.public_id == invoiceId, Invoice.account_id == acct.id)
            .options(selectinload(Invoice.line_items))
        )
    ).scalar_one_or_none()
    if inv is None:
        raise not_found("Invoice not found")
    return InvoiceRead(
        invoiceId=inv.public_id,
        accountId=acct.public_id,
        period=inv.period,
        totalAmount=inv.total_amount,
        currency=inv.currency,
        status=inv.status,
        issuedAt=inv.issued_at,
        lineItems=[
            InvoiceLineItemSchema(
                description=li.description,
                amount=li.amount,
                currency=li.currency,
                relatedProductId=li.related_product_public_id,
                relatedPlanId=li.related_plan_public_id,
            )
            for li in inv.line_items
        ],
    )


@router.get("/me/invoices/{invoiceId}/download")
async def download_invoice(
    invoiceId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    acct = await _customer_account(session, customer)
    inv = (
        await session.execute(
            select(Invoice).where(Invoice.public_id == invoiceId, Invoice.account_id == acct.id)
        )
    ).scalar_one_or_none()
    if inv is None:
        raise not_found("Invoice not found")
    # Minimal valid PDF that says "VulnMNO Invoice <id>". A real PDF renderer is out of phase 1.
    body_text = f"VulnMNO Invoice {inv.public_id} period {inv.period}\n"
    pdf = _minimal_pdf(body_text)
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{inv.public_id}.pdf"'},
    )


def _minimal_pdf(text: str) -> bytes:
    escaped = text.replace("(", "\\(").replace(")", "\\)")
    body = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/"
        b"Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    )
    stream = f"BT /F1 12 Tf 50 750 Td ({escaped}) Tj ET".encode()
    body += b"4 0 obj<</Length " + str(len(stream)).encode() + b">>stream\n" + stream + b"\nendstream endobj\n"
    body += b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    body += b"xref\n0 6\n0000000000 65535 f \n"
    body += b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n0\n%%EOF\n"
    return body


@router.post(
    "/me/refunds", response_model=RefundCreated, status_code=status.HTTP_202_ACCEPTED
)
async def request_refund(
    body: RefundRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    # Validate target exists and belongs to caller
    if body.targetType == "purchase":
        target = (
            await session.execute(
                select(Purchase).where(
                    Purchase.public_id == body.targetId, Purchase.customer_id == customer.id
                )
            )
        ).scalar_one_or_none()
        if target is None:
            raise not_found("Purchase not found")
    else:
        acct = await _customer_account(session, customer)
        target = (
            await session.execute(
                select(Invoice).where(
                    Invoice.public_id == body.targetId, Invoice.account_id == acct.id
                )
            )
        ).scalar_one_or_none()
        if target is None:
            raise not_found("Invoice not found")

    ticket = SupportTicket(
        public_id=await next_ticket_id(session),
        customer_id=customer.id,
        topic="Billing",
        description=f"Refund requested for {body.targetType} {body.targetId}: {body.reason}",
        status="open",
    )
    session.add(ticket)
    await session.flush()
    session.add(
        TicketMessage(
            public_id=f"MSG-{ticket.id + 49000}",
            ticket_id=ticket.id,
            author_role="system",
            author_display_name="Refund workflow",
            body=body.reason,
        )
    )
    refund = Refund(
        public_id=await next_refund_id(session),
        customer_id=customer.id,
        target_type=body.targetType,
        target_public_id=body.targetId,
        reason=body.reason,
        ticket_id=ticket.id,
    )
    session.add(refund)
    await session.flush()
    await write_audit(
        session,
        event_type="REFUND_REQUESTED",
        actor_id=customer.public_id,
        target_type=body.targetType,
        target_id=body.targetId,
        payload={"refundId": refund.public_id, "reason": body.reason},
    )
    return RefundCreated(refundId=refund.public_id, ticketId=ticket.public_id)
