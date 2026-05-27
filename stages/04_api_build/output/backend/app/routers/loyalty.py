from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_customer, get_session
from app.errors import not_found
from app.models import Customer, LoyaltyAccount, LoyaltyTier, LoyaltyTransaction, Purchase
from app.schemas.common import Page
from app.schemas.loyalty import LoyaltyAccountRead, LoyaltyTransactionRead
from app.services.pagination import paginate

router = APIRouter(prefix="/api/loyalty", tags=["loyalty"])

_TIER_ORDER = ["bronze", "silver", "gold", "platinum"]


@router.get("/account", response_model=LoyaltyAccountRead)
async def loyalty_account(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    account = (
        await session.execute(select(LoyaltyAccount).where(LoyaltyAccount.customer_id == customer.id))
    ).scalar_one_or_none()
    if account is None:
        raise not_found("Loyalty account not found")

    tiers = {t.name: t for t in (await session.execute(select(LoyaltyTier))).scalars().all()}
    current = tiers.get(account.tier)
    multiplier = Decimal(current.multiplier) if current else Decimal("1.00")

    # Determine next tier (if any).
    next_tier = None
    points_to_next = None
    idx = _TIER_ORDER.index(account.tier) if account.tier in _TIER_ORDER else 0
    if idx + 1 < len(_TIER_ORDER):
        nxt_name = _TIER_ORDER[idx + 1]
        nxt = tiers.get(nxt_name)
        if nxt is not None and nxt.threshold_lifetime_points > account.lifetime_points:
            next_tier = nxt_name
            points_to_next = nxt.threshold_lifetime_points - account.lifetime_points

    return LoyaltyAccountRead(
        customerId=customer.public_id,
        points=account.points,
        lifetimePoints=account.lifetime_points,
        tier=account.tier,
        multiplier=multiplier,
        nextTier=next_tier,
        pointsToNextTier=points_to_next,
    )


@router.get("/transactions", response_model=Page[LoyaltyTransactionRead])
async def loyalty_transactions(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    account = (
        await session.execute(select(LoyaltyAccount).where(LoyaltyAccount.customer_id == customer.id))
    ).scalar_one_or_none()
    if account is None:
        return Page(items=[], nextCursor=None)

    stmt = select(LoyaltyTransaction).where(LoyaltyTransaction.account_id == account.id)
    rows, nxt = await paginate(session, stmt, id_column=LoyaltyTransaction.id, limit=limit, cursor=cursor)

    purchase_public = {}
    pur_ids = {r.related_purchase_id for r in rows if r.related_purchase_id is not None}
    if pur_ids:
        for p in (
            await session.execute(select(Purchase).where(Purchase.id.in_(pur_ids)))
        ).scalars().all():
            purchase_public[p.id] = p.public_id

    items = [
        LoyaltyTransactionRead(
            transactionId=t.public_id,
            accountId=account.public_id,
            delta=t.delta,
            balanceAfter=t.balance_after,
            reason=t.reason,
            relatedPurchaseId=purchase_public.get(t.related_purchase_id),
            timestamp=t.timestamp,
        )
        for t in rows
    ]
    return Page(items=items, nextCursor=nxt)
