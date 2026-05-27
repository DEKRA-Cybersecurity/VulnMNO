"""Idempotent seed loader.

Running twice produces the same database state. Re-runnable via:

    python -m app.seed

or programmatically from `app.main` lifespan in stage 04.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine, session_scope
from app.models import (
    Account,
    Balance,
    Base,
    Coupon,
    Customer,
    Invoice,
    InvoiceLineItem,
    MobileLine,
    Notification,
    Plan,
    Product,
    Promotion,
    SIMProfile,
    SupportTicket,
    TicketMessage,
    UsageRecord,
)

# --- demo password hashing -----------------------------------------------------
# Stage 04 swaps this for Argon2id (per auth-model.md). For phase-1 seed we use
# a deterministic SHA-256 + salt so the seed is reproducible without depending
# on argon2-cffi at seed time. Stage 04's password verifier accepts both
# during a one-time migration window, then drops this format.

SEED_PASSWORD = "secret123"
SEED_SALT = "vulnmno-seed-salt"


def seed_password_hash(plain: str = SEED_PASSWORD) -> str:
    return "seed$" + hashlib.sha256((SEED_SALT + plain).encode()).hexdigest()


# --- helpers -------------------------------------------------------------------

UTC = timezone.utc


async def _get_or_create(
    session: AsyncSession,
    model: type,
    *,
    lookup: dict,
    defaults: dict | None = None,
) -> tuple[object, bool]:
    """Idempotency primitive: select by `lookup`, otherwise insert lookup+defaults."""
    stmt = select(model).filter_by(**lookup)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj is not None:
        return obj, False
    payload = {**lookup, **(defaults or {})}
    obj = model(**payload)
    session.add(obj)
    await session.flush()
    return obj, True


# --- seeds ---------------------------------------------------------------------

async def seed_plans(session: AsyncSession) -> dict[str, Plan]:
    plans = {
        "PREPAID-BASIC": dict(
            name="Prepaid Basic",
            description="500 MB / 100 min / 100 SMS, pay-as-you-go.",
            monthly_price=Decimal("0.00"),
            data_limit_mb=500,
            voice_limit_min=100,
            sms_limit=100,
            category="prepaid",
            available_services=["voicemail", "caller_id"],
        ),
        "PREPAID-PLUS": dict(
            name="Prepaid Plus",
            description="5 GB / unlimited calls within Spain.",
            monthly_price=Decimal("12.99"),
            data_limit_mb=5_000,
            voice_limit_min=-1,
            sms_limit=500,
            category="prepaid",
            available_services=["voicemail", "caller_id", "wifi_calling"],
        ),
        "UNLIMITED-PREMIUM": dict(
            name="Unlimited Premium",
            description="Unlimited data, voice and SMS plus EU roaming.",
            monthly_price=Decimal("39.99"),
            data_limit_mb=-1,
            voice_limit_min=-1,
            sms_limit=-1,
            category="postpaid",
            available_services=["voicemail", "caller_id", "wifi_calling", "roaming_eu"],
        ),
        "STUDENT-25": dict(
            name="Student 25",
            description="25 GB data, unlimited calls; age verification required.",
            monthly_price=Decimal("19.99"),
            data_limit_mb=25_000,
            voice_limit_min=-1,
            sms_limit=-1,
            category="student",
            eligibility_rules={"max_age": 26},
            available_services=["voicemail", "caller_id"],
        ),
    }
    out: dict[str, Plan] = {}
    for pid, defaults in plans.items():
        plan, _ = await _get_or_create(
            session, Plan, lookup={"public_id": pid}, defaults=defaults
        )
        out[pid] = plan  # type: ignore[assignment]
    return out


async def seed_products(session: AsyncSession) -> dict[str, Product]:
    products = {
        "DATA-10GB-7D": dict(
            name="10 GB Data Bundle",
            description="10 GB valid for 7 days.",
            category="data_bundle",
            price=Decimal("9.99"),
            validity_days=7,
            eligible_plans=["PREPAID-BASIC", "PREPAID-PLUS"],
            featured=True,
        ),
        "DATA-5GB-30D": dict(
            name="5 GB Data Bundle",
            description="5 GB valid for 30 days.",
            category="data_bundle",
            price=Decimal("7.50"),
            validity_days=30,
            eligible_plans=["PREPAID-BASIC", "PREPAID-PLUS"],
        ),
        "ROAMING-EU": dict(
            name="EU Roaming Pack",
            description="3 GB EU roaming for 14 days.",
            category="roaming",
            price=Decimal("14.99"),
            validity_days=14,
            eligible_plans=["PREPAID-PLUS", "UNLIMITED-PREMIUM"],
        ),
        "VOICE-200MIN": dict(
            name="200 Voice Minutes",
            description="200 minutes valid for 30 days.",
            category="voice_bundle",
            price=Decimal("4.99"),
            validity_days=30,
            eligible_plans=["PREPAID-BASIC", "PREPAID-PLUS"],
        ),
    }
    out: dict[str, Product] = {}
    for pid, defaults in products.items():
        prod, _ = await _get_or_create(
            session, Product, lookup={"public_id": pid}, defaults=defaults
        )
        out[pid] = prod  # type: ignore[assignment]
    return out


async def seed_promotions(session: AsyncSession) -> dict[str, Promotion]:
    now = datetime(2026, 5, 1, tzinfo=UTC)
    promos = {
        "PROMO-SUMMER-2026": dict(
            name="Summer Discount 2026",
            description="20% off any data bundle.",
            discount_type="percent",
            discount_value=Decimal("20.00"),
            starts_at=now,
            ends_at=now + timedelta(days=120),
            eligible_product_ids=["DATA-10GB-7D", "DATA-5GB-30D"],
            combinable=True,
        ),
        "PROMO-LOYALTY": dict(
            name="Loyalty discount",
            description="10% off for gold/platinum customers.",
            discount_type="percent",
            discount_value=Decimal("10.00"),
            starts_at=now - timedelta(days=30),
            ends_at=now + timedelta(days=365),
            eligibility_rules={"min_loyalty_tier": "gold"},
            combinable=True,
        ),
        "PROMO-FIRST": dict(
            name="First purchase 50%",
            description="50% off the first purchase, once per customer.",
            discount_type="percent",
            discount_value=Decimal("50.00"),
            starts_at=now - timedelta(days=30),
            ends_at=now + timedelta(days=365),
            eligibility_rules={"max_prior_purchases": 0},
            combinable=False,
        ),
    }
    out: dict[str, Promotion] = {}
    for pid, defaults in promos.items():
        promo, _ = await _get_or_create(
            session, Promotion, lookup={"public_id": pid}, defaults=defaults
        )
        out[pid] = promo  # type: ignore[assignment]
    return out


async def seed_coupons(session: AsyncSession, promos: dict[str, Promotion]) -> None:
    coupons = [
        ("SUMMER20", promos["PROMO-SUMMER-2026"], 10000),
        ("GOLD10", promos["PROMO-LOYALTY"], 10000),
        ("WELCOME50", promos["PROMO-FIRST"], 10000),
    ]
    for code, promo, limit in coupons:
        await _get_or_create(
            session,
            Coupon,
            lookup={"code": code},
            defaults={"promotion_id": promo.id, "usage_limit": limit},
        )


async def seed_customers(session: AsyncSession, plans: dict[str, Plan]) -> dict[str, Customer]:
    spec = [
        dict(
            public_id="CUST-10001",
            name="Alice García",
            email="alice@example.test",
            primary_msisdn="+34600000001",
            account_type="prepaid",
            loyalty_tier="silver",
            otp_enrolled=False,
            plan_public_id="PREPAID-PLUS",
            line_public_id="LINE-10001",
            sim_public_id="SIM-10001",
            iccid="8934075000000000001",
            initial_balance=Decimal("25.50"),
        ),
        dict(
            public_id="CUST-10002",
            name="Bruno López",
            email="bruno@example.test",
            primary_msisdn="+34600000002",
            account_type="postpaid",
            loyalty_tier="gold",
            otp_enrolled=True,
            otp_fixed_code="123456",
            plan_public_id="UNLIMITED-PREMIUM",
            line_public_id="LINE-10002",
            sim_public_id="SIM-10002",
            iccid="8934075000000000002",
            initial_balance=Decimal("0.00"),
        ),
        dict(
            public_id="CUST-10003",
            name="Clara Núñez",
            email="clara@example.test",
            primary_msisdn="+34600000003",
            account_type="hybrid",
            loyalty_tier="bronze",
            otp_enrolled=False,
            plan_public_id="STUDENT-25",
            line_public_id="LINE-10003",
            sim_public_id="SIM-10003",
            iccid="8934075000000000003",
            initial_balance=Decimal("12.00"),
        ),
    ]
    out: dict[str, Customer] = {}
    for s in spec:
        customer, created = await _get_or_create(
            session,
            Customer,
            lookup={"public_id": s["public_id"]},
            defaults={
                "name": s["name"],
                "email": s["email"],
                "primary_msisdn": s["primary_msisdn"],
                "account_type": s["account_type"],
                "loyalty_tier": s["loyalty_tier"],
                "password_hash": seed_password_hash(),
                "otp_enrolled": s["otp_enrolled"],
                "otp_fixed_code": s.get("otp_fixed_code"),
            },
        )
        # Account + balance
        account, _ = await _get_or_create(
            session,
            Account,
            lookup={"customer_id": customer.id},
            defaults={
                "public_id": s["public_id"].replace("CUST-", "ACC-"),
                "account_type": s["account_type"],
            },
        )
        await _get_or_create(
            session,
            Balance,
            lookup={"account_id": account.id},
            defaults={"amount": s["initial_balance"], "currency": "EUR"},
        )
        # SIM + line
        sim, _ = await _get_or_create(
            session,
            SIMProfile,
            lookup={"public_id": s["sim_public_id"]},
            defaults={
                "iccid": s["iccid"],
                "imsi_alias": s["sim_public_id"],
                "sim_type": "esim" if s["public_id"].endswith("3") else "physical",
                "activation_date": date(2026, 1, 15),
            },
        )
        plan = plans[s["plan_public_id"]]
        await _get_or_create(
            session,
            MobileLine,
            lookup={"public_id": s["line_public_id"]},
            defaults={
                "msisdn": s["primary_msisdn"],
                "customer_id": customer.id,
                "plan_id": plan.id,
                "sim_id": sim.id,
                "activated_at": date(2026, 1, 15),
            },
        )
        out[s["public_id"]] = customer  # type: ignore[assignment]
    return out


async def seed_usage(session: AsyncSession) -> None:
    """Seed a handful of usage records against LINE-10001 in May 2026."""
    base = datetime(2026, 5, 10, 9, 0, tzinfo=UTC)
    rows = [
        dict(
            public_id="USG-70001",
            type="call",
            direction="outgoing",
            destination="+34600000099",
            started_at=base,
            duration_seconds=180,
            cost=Decimal("0.15"),
        ),
        dict(
            public_id="USG-70002",
            type="sms",
            direction="outgoing",
            destination="+34600000099",
            started_at=base + timedelta(hours=2),
            cost=Decimal("0.05"),
        ),
        dict(
            public_id="USG-70003",
            type="data",
            started_at=base + timedelta(days=1),
            duration_seconds=600,
            volume_megabytes=Decimal("123.456"),
            cost=Decimal("0.00"),
            network_type="LTE",
        ),
        dict(
            public_id="USG-70004",
            type="roaming",
            started_at=base + timedelta(days=2),
            duration_seconds=300,
            volume_megabytes=Decimal("45.000"),
            cost=Decimal("1.20"),
            country="FR",
            network_type="LTE",
            roaming=True,
        ),
    ]
    # Find LINE-10001
    line = (await session.execute(
        select(MobileLine).where(MobileLine.public_id == "LINE-10001")
    )).scalar_one_or_none()
    if line is None:
        return
    for r in rows:
        await _get_or_create(
            session,
            UsageRecord,
            lookup={"public_id": r["public_id"]},
            defaults={**r, "line_id": line.id},
        )


async def seed_invoices(session: AsyncSession) -> None:
    """One invoice for Bruno (postpaid) for the May 2026 period."""
    customer = (await session.execute(
        select(Customer).where(Customer.public_id == "CUST-10002")
    )).scalar_one_or_none()
    if customer is None:
        return
    account = (await session.execute(
        select(Account).where(Account.customer_id == customer.id)
    )).scalar_one()
    inv, created = await _get_or_create(
        session,
        Invoice,
        lookup={"public_id": "INV-20001"},
        defaults={
            "account_id": account.id,
            "period": "2026-05",
            "total_amount": Decimal("39.99"),
            "status": "issued",
            "issued_at": datetime(2026, 6, 1, 0, 0, tzinfo=UTC),
        },
    )
    if created:
        session.add(InvoiceLineItem(
            invoice_id=inv.id,
            description="Unlimited Premium — monthly",
            amount=Decimal("39.99"),
            related_plan_public_id="UNLIMITED-PREMIUM",
        ))


async def seed_support(session: AsyncSession) -> None:
    customer = (await session.execute(
        select(Customer).where(Customer.public_id == "CUST-10001")
    )).scalar_one_or_none()
    if customer is None:
        return
    ticket, created = await _get_or_create(
        session,
        SupportTicket,
        lookup={"public_id": "TCK-30001"},
        defaults={
            "customer_id": customer.id,
            "topic": "Billing",
            "description": "Charged twice for the 10 GB bundle on May 12.",
            "status": "open",
        },
    )
    if created:
        session.add(TicketMessage(
            public_id="MSG-40001",
            ticket_id=ticket.id,
            author_role="customer",
            author_display_name="Alice García",
            body="Charged twice for the 10 GB bundle on May 12.",
        ))


async def seed_notifications(session: AsyncSession) -> None:
    customer = (await session.execute(
        select(Customer).where(Customer.public_id == "CUST-10001")
    )).scalar_one_or_none()
    if customer is None:
        return
    await _get_or_create(
        session,
        Notification,
        lookup={"public_id": "NTF-50001"},
        defaults={
            "customer_id": customer.id,
            "channel": "in_app",
            "message_type": "promotion",
            "title": "Summer discount available",
            "body": "Use SUMMER20 for 20% off any data bundle.",
        },
    )


# --- entry point ---------------------------------------------------------------

async def run_seed() -> None:
    # Create tables if they do not exist yet (idempotent).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_scope() as session:
        plans = await seed_plans(session)
        await seed_products(session)
        promos = await seed_promotions(session)
        await seed_coupons(session, promos)
        await seed_customers(session, plans)
        await seed_usage(session)
        await seed_invoices(session)
        await seed_support(session)
        await seed_notifications(session)
    print("seed: ok")


if __name__ == "__main__":
    asyncio.run(run_seed())
