from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import AppError, ErrorCode, bad_request
from app.models import Coupon, Customer, Product, Promotion
from datetime import datetime, timezone

from app.security import now


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

LOYALTY_RANK = {"bronze": 0, "silver": 1, "gold": 2, "platinum": 3}


async def resolve_promo(
    session: AsyncSession,
    *,
    customer: Customer,
    product: Product,
    promo_code: str,
) -> tuple[Promotion, Decimal, Decimal]:
    """Returns (promotion, discount_amount, final_price). Raises AppError on invalid/ineligible."""
    coupon = (
        await session.execute(select(Coupon).where(Coupon.code == promo_code))
    ).scalar_one_or_none()
    if coupon is None or coupon.status != "active":
        raise bad_request(ErrorCode.PROMO_INVALID, "Promotion code is not valid")
    if coupon.usage_count >= coupon.usage_limit:
        raise bad_request(ErrorCode.PROMO_INVALID, "Promotion code is exhausted")

    promo = (
        await session.execute(select(Promotion).where(Promotion.id == coupon.promotion_id))
    ).scalar_one_or_none()
    if promo is None:
        raise bad_request(ErrorCode.PROMO_INVALID, "Promotion not found")
    current = now()
    if not (_aware(promo.starts_at) <= current <= _aware(promo.ends_at)):
        raise bad_request(ErrorCode.PROMO_INVALID, "Promotion not active")

    eligible_ids = promo.eligible_product_ids or []
    if eligible_ids and product.public_id not in eligible_ids:
        raise bad_request(
            ErrorCode.PROMO_INELIGIBLE, "Product not eligible", rule="eligible_product_ids"
        )

    rules = promo.eligibility_rules or {}
    if "min_loyalty_tier" in rules:
        if LOYALTY_RANK.get(customer.loyalty_tier, 0) < LOYALTY_RANK.get(rules["min_loyalty_tier"], 0):
            raise bad_request(
                ErrorCode.PROMO_INELIGIBLE, "Loyalty tier too low", rule="loyalty_tier"
            )
    if "max_prior_purchases" in rules:
        from app.models import Purchase  # local to avoid cycle

        prior = (
            await session.execute(
                select(Purchase).where(
                    Purchase.customer_id == customer.id, Purchase.status == "confirmed"
                )
            )
        ).scalars().all()
        if len(prior) > int(rules["max_prior_purchases"]):
            raise bad_request(
                ErrorCode.PROMO_INELIGIBLE, "Already used", rule="prior_purchases"
            )

    if promo.discount_type == "percent":
        discount = (product.price * promo.discount_value / Decimal("100")).quantize(Decimal("0.01"))
    else:
        discount = promo.discount_value
    final = product.price - discount
    if final < 0:
        final = Decimal("0.00")
        discount = product.price
    return promo, discount, final
