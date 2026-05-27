"""Refund workflow side effects — called by the admin portal's refund approve endpoint.

Stage 11 marks `Refund.status='approved'` and appends a `TicketMessage`. This service
extends that with the wallet-credit `Transaction` so the customer actually gets refunded.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ids import next_transaction_id
from app.models import Account, Balance, Invoice, Purchase, Refund, Transaction

log = logging.getLogger("vulnmno.refund")


async def credit_wallet_for_refund(
    session: AsyncSession, *, refund: Refund
) -> Transaction | None:
    """Create the refund Transaction crediting the customer's wallet. Returns the row,
    or None if the refund target cannot be resolved.
    """
    amount = await _resolve_amount(session, refund=refund)
    if amount is None:
        log.warning("refund %s — cannot resolve amount; skipping wallet credit", refund.public_id)
        return None

    account = (
        await session.execute(select(Account).where(Account.customer_id == refund.customer_id))
    ).scalar_one_or_none()
    if account is None:
        log.warning("refund %s — no account for customer %d", refund.public_id, refund.customer_id)
        return None
    balance = (
        await session.execute(select(Balance).where(Balance.account_id == account.id))
    ).scalar_one()

    balance.amount = (balance.amount or Decimal("0.00")) + amount
    tx = Transaction(
        public_id=await next_transaction_id(session),
        account_id=account.id,
        type="refund",
        amount=amount,
        currency=balance.currency,
        balance_after=balance.amount,
    )
    session.add(tx)
    await session.flush()
    return tx


async def _resolve_amount(session: AsyncSession, *, refund: Refund) -> Decimal | None:
    if refund.target_type == "purchase":
        p = (
            await session.execute(select(Purchase).where(Purchase.public_id == refund.target_public_id))
        ).scalar_one_or_none()
        return p.final_price if p is not None else None
    if refund.target_type == "invoice":
        inv = (
            await session.execute(select(Invoice).where(Invoice.public_id == refund.target_public_id))
        ).scalar_one_or_none()
        return inv.total_amount if inv is not None else None
    return None
