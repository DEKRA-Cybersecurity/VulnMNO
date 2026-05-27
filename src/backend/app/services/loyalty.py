"""Loyalty engine — accrual + tier transition.

Hook called from `routers/shop.py::create_purchase` post-confirm:

    await accrue_for_purchase(session, customer=customer, purchase=purchase)

Reads the customer's current tier multiplier from `loyalty_tiers`, computes
`points = floor(final_price * multiplier)`, writes a `LoyaltyTransaction(reason="purchase")`,
recomputes `points`/`lifetime_points`, and promotes tier if a threshold is crossed.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Customer,
    LoyaltyAccount,
    LoyaltyTier,
    LoyaltyTransaction,
    Purchase,
)

log = logging.getLogger("vulnmno.loyalty")

_TIER_ORDER = ["bronze", "silver", "gold", "platinum"]


async def _next_loyalty_tx_id(session: AsyncSession) -> str:
    from sqlalchemy import func
    n = (await session.execute(select(func.count()).select_from(LoyaltyTransaction))).scalar_one()
    return f"LTX-{70000 + int(n) + 1}"


async def accrue_for_purchase(
    session: AsyncSession,
    *,
    customer: Customer,
    purchase: Purchase,
) -> int:
    """Returns the points awarded (0 if the customer has no loyalty account)."""
    account = (
        await session.execute(select(LoyaltyAccount).where(LoyaltyAccount.customer_id == customer.id))
    ).scalar_one_or_none()
    if account is None:
        log.info("no loyalty account for %s — skipping accrual", customer.public_id)
        return 0

    tier_row = (
        await session.execute(select(LoyaltyTier).where(LoyaltyTier.name == account.tier))
    ).scalar_one_or_none()
    multiplier = Decimal(tier_row.multiplier) if tier_row else Decimal("1.00")
    delta = int((purchase.final_price * multiplier).to_integral_value())
    if delta <= 0:
        return 0

    new_points = account.points + delta
    new_lifetime = account.lifetime_points + delta
    account.points = new_points
    account.lifetime_points = new_lifetime

    # Tier promotion ONLY — never downgrade based on lifetime_points alone, since
    # the seed/admin may set a higher initial tier manually (e.g. comped).
    candidate = await _resolve_tier(session, new_lifetime)
    if _TIER_ORDER.index(candidate) > _TIER_ORDER.index(account.tier):
        log.info("loyalty: %s tier %s → %s", customer.public_id, account.tier, candidate)
        account.tier = candidate
        customer.loyalty_tier = candidate

    session.add(
        LoyaltyTransaction(
            public_id=await _next_loyalty_tx_id(session),
            account_id=account.id,
            delta=delta,
            balance_after=new_points,
            reason="purchase",
            related_purchase_id=purchase.id,
        )
    )
    return delta


async def _resolve_tier(session: AsyncSession, lifetime_points: int) -> str:
    tiers = (await session.execute(select(LoyaltyTier))).scalars().all()
    # Highest tier whose threshold ≤ lifetime_points.
    sorted_tiers = sorted(tiers, key=lambda t: t.threshold_lifetime_points)
    current = "bronze"
    for t in sorted_tiers:
        if lifetime_points >= t.threshold_lifetime_points:
            current = t.name
    return current
