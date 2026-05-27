"""Idempotent Phase-2 seed: admin users (one per role) + loyalty tiers + loyalty accounts.

Run after `app.seed` has populated Phase-1 customers. Re-runnable: existing rows are left
untouched (matched by `username` / `name` / `customer_id`).

    python -m app.seed_phase2
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine, session_scope
from app.models import (
    AdminUser,
    Base,
    Customer,
    LoyaltyAccount,
    LoyaltyTier,
)
from app.security import hash_password


SEED_ADMIN_PASSWORD = "admin1234"


async def _get_or_create(
    session: AsyncSession,
    model: type,
    *,
    lookup: dict,
    defaults: dict | None = None,
) -> tuple[object, bool]:
    stmt = select(model).filter_by(**lookup)
    obj = (await session.execute(stmt)).scalar_one_or_none()
    if obj is not None:
        return obj, False
    obj = model(**{**lookup, **(defaults or {})})
    session.add(obj)
    await session.flush()
    return obj, True


async def seed_admin_users(session: AsyncSession) -> None:
    spec = [
        ("support",  "support_agent",     "Sara Soporte"),
        ("billing",  "billing_operator",  "Borja Billing"),
        ("product",  "product_manager",   "Paula Producto"),
        ("ops",      "ops_admin",         "Olivia Ops"),
        ("security", "security_analyst",  "Saúl Security"),
        # supplier_admin role exists but no Phase 2 permissions; intentional omission.
    ]
    pwhash = hash_password(SEED_ADMIN_PASSWORD)
    for i, (username, role, full_name) in enumerate(spec, start=1):
        await _get_or_create(
            session,
            AdminUser,
            lookup={"username": username},
            defaults={
                "public_id": f"ADM-{10000 + i}",
                "password_hash": pwhash,
                "role": role,
                "full_name": full_name,
                "status": "active",
            },
        )


async def seed_loyalty_tiers(session: AsyncSession) -> None:
    spec = [
        ("bronze",   0,     Decimal("1.00")),
        ("silver",   500,   Decimal("1.20")),
        ("gold",     2000,  Decimal("1.50")),
        ("platinum", 10000, Decimal("2.00")),
    ]
    for name, threshold, multiplier in spec:
        await _get_or_create(
            session,
            LoyaltyTier,
            lookup={"name": name},
            defaults={
                "threshold_lifetime_points": threshold,
                "multiplier": multiplier,
            },
        )


async def seed_loyalty_accounts(session: AsyncSession) -> None:
    customers = (await session.execute(select(Customer))).scalars().all()
    for i, c in enumerate(customers, start=1):
        await _get_or_create(
            session,
            LoyaltyAccount,
            lookup={"customer_id": c.id},
            defaults={
                "public_id": f"LACC-{60000 + i}",
                "points": 0,
                "lifetime_points": 0,
                "tier": c.loyalty_tier,
            },
        )


async def run_seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_scope() as session:
        await seed_admin_users(session)
        await seed_loyalty_tiers(session)
        await seed_loyalty_accounts(session)
    print("seed_phase2: ok")


if __name__ == "__main__":
    asyncio.run(run_seed())
