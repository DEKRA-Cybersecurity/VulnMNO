from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.errors import AppError, ErrorCode, not_found
from app.ids import next_transaction_id
from app.models import (
    Account,
    AdminUser,
    Balance,
    Customer,
    MobileLine,
    Plan,
    Purchase,
    SupportTicket,
    Transaction,
)
from app.services.pagination import paginate

from ..deps import get_current_admin, require_csrf, require_module
from ..permissions import Access, Module
from ..services.audit import write_admin_audit
from ..templates_loader import render

router = APIRouter(prefix="/admin/customers")


@router.get("")
async def search(
    request: Request,
    admin: Annotated[AdminUser, Depends(require_module(Module.CUSTOMER_SEARCH, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
    q: str = "",
    limit: int = 20,
):
    rows: list[Customer] = []
    if q:
        term = f"%{q}%"
        rows = (
            await session.execute(
                select(Customer)
                .where(
                    or_(
                        Customer.primary_msisdn.like(term),
                        Customer.public_id.like(term),
                        Customer.name.like(term),
                        Customer.email.like(term),
                    ),
                    Customer.deleted_at.is_(None),
                )
                .limit(limit)
            )
        ).scalars().all()
    tpl = "admin/_partials/customers_table.html" if request.headers.get("HX-Request") == "true" else "admin/customers/search.html"
    return render(request, tpl, {"q": q, "rows": rows})


@router.get("/{customerId}")
async def detail(
    request: Request,
    customerId: str,
    admin: Annotated[AdminUser, Depends(require_module(Module.CUSTOMER_SEARCH, Access.READ))],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    customer = (
        await session.execute(select(Customer).where(Customer.public_id == customerId))
    ).scalar_one_or_none()
    if customer is None or customer.deleted_at is not None:
        raise not_found("Customer not found")

    account = (
        await session.execute(select(Account).where(Account.customer_id == customer.id))
    ).scalar_one_or_none()
    balance = None
    if account is not None:
        balance = (
            await session.execute(select(Balance).where(Balance.account_id == account.id))
        ).scalar_one_or_none()

    lines = (
        await session.execute(
            select(MobileLine).where(MobileLine.customer_id == customer.id, MobileLine.deleted_at.is_(None))
        )
    ).scalars().all()

    current_plan = None
    if lines and lines[0].plan_id is not None:
        current_plan = (
            await session.execute(select(Plan).where(Plan.id == lines[0].plan_id))
        ).scalar_one_or_none()

    recent_tx = (
        await session.execute(
            select(Transaction).where(Transaction.account_id == account.id if account else False)
            .order_by(Transaction.id.desc()).limit(10)
        )
    ).scalars().all() if account else []

    recent_pur = (
        await session.execute(
            select(Purchase).where(Purchase.customer_id == customer.id)
            .order_by(Purchase.id.desc()).limit(10)
        )
    ).scalars().all()

    open_tickets = (
        await session.execute(
            select(SupportTicket).where(
                SupportTicket.customer_id == customer.id,
                SupportTicket.status != "closed",
            ).order_by(SupportTicket.id.desc()).limit(5)
        )
    ).scalars().all()

    can_adjust_balance = admin.role in ("billing_operator", "ops_admin")

    return render(
        request,
        "admin/customers/detail.html",
        {
            "customer": customer,
            "account": account,
            "balance": balance,
            "lines": lines,
            "current_plan": current_plan,
            "recent_tx": recent_tx,
            "recent_pur": recent_pur,
            "open_tickets": open_tickets,
            "can_adjust_balance": can_adjust_balance,
        },
    )


@router.post("/{customerId}/balance-adjust")
async def balance_adjust(
    request: Request,
    customerId: str,
    amount: Annotated[str, Form()],
    reason: Annotated[str, Form()],
    admin: Annotated[AdminUser, Depends(require_module(Module.CUSTOMER_BALANCE, Access.READ_WRITE))],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    try:
        delta = Decimal(amount)
    except InvalidOperation:
        raise AppError(ErrorCode.VALIDATION_FAILED, "Amount must be a decimal number", http_status=400)
    if abs(delta) > Decimal("500.00"):
        raise AppError(ErrorCode.VALIDATION_FAILED, "Amount magnitude must be ≤ €500", http_status=400)
    if len(reason) < 10:
        raise AppError(ErrorCode.VALIDATION_FAILED, "Reason must be ≥ 10 chars", http_status=400)

    customer = (
        await session.execute(select(Customer).where(Customer.public_id == customerId))
    ).scalar_one_or_none()
    if customer is None:
        raise not_found("Customer not found")
    account = (
        await session.execute(select(Account).where(Account.customer_id == customer.id))
    ).scalar_one_or_none()
    if account is None:
        raise not_found("Account not found")
    balance = (
        await session.execute(select(Balance).where(Balance.account_id == account.id))
    ).scalar_one()

    balance.amount = (balance.amount or Decimal("0.00")) + delta
    session.add(
        Transaction(
            public_id=await next_transaction_id(session),
            account_id=account.id,
            type="adjustment",
            amount=delta,
            currency=balance.currency,
            balance_after=balance.amount,
        )
    )
    await write_admin_audit(
        session,
        admin=admin,
        event_type="ADMIN_BALANCE_ADJUSTMENT",
        target_type="customer",
        target_id=customer.public_id,
        payload={"delta": str(delta), "reason": reason, "balance_after": str(balance.amount)},
        request=request,
    )
    await session.flush()
    # Re-fetch a fresh Balance row so server-side onupdate columns materialize and the
    # Jinja template render doesn't fire a sync lazy-load inside the async event loop.
    balance = (
        await session.execute(select(Balance).where(Balance.id == balance.id))
    ).scalar_one()
    return render(
        request,
        "admin/_partials/balance_card.html",
        {
            "customer": customer,
            "balance": balance,
            "flash": f"Balance updated: {balance.amount} {balance.currency}",
            "can_adjust_balance": True,
        },
    )
