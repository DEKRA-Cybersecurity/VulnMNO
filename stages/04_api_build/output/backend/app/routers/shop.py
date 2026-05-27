from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import IdempotencyKey, get_current_customer, get_session
from app.errors import AppError, ErrorCode, conflict, not_found
from app.ids import next_purchase_id, next_transaction_id
from app.models import (
    Account,
    Balance,
    Coupon,
    Customer,
    Product,
    Purchase,
    Transaction,
)
from app.schemas.common import Page
from app.schemas.shop import (
    ApplyPromoRequest,
    CreatePurchaseRequest,
    ProductRead,
    PromoApplicationRead,
    ProvisioningStatus,
    PurchaseRead,
)
from app.services.audit import write_audit
from app.services.pagination import paginate
from app.services.shop import resolve_promo

router = APIRouter(prefix="/api/shop", tags=["shop"])
UTC = timezone.utc


def _product_read(p: Product) -> ProductRead:
    return ProductRead(
        productId=p.public_id,
        name=p.name,
        category=p.category,
        description=p.description,
        price=p.price,
        currency=p.currency,
        validityDays=p.validity_days,
        eligiblePlans=p.eligible_plans or [],
        featured=p.featured,
        availability=p.availability,
    )


def _purchase_read(p: Purchase, customer: Customer, product: Product) -> PurchaseRead:
    return PurchaseRead(
        purchaseId=p.public_id,
        customerId=customer.public_id,
        productId=product.public_id,
        promotionId=None,
        status=p.status,
        originalPrice=p.original_price,
        finalPrice=p.final_price,
        currency=p.currency,
        createdAt=p.created_at,
        provisioning=ProvisioningStatus(
            status=p.provisioning_status, activatedAt=p.provisioning_activated_at
        ),
    )


@router.get("/products", response_model=Page[ProductRead])
async def list_products(
    _: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    category: str | None = None,
    featured: bool | None = None,
):
    stmt = select(Product).where(Product.availability != "hidden")
    if category:
        stmt = stmt.where(Product.category == category)
    if featured is not None:
        stmt = stmt.where(Product.featured == featured)
    rows, nxt = await paginate(session, stmt, id_column=Product.id, limit=limit, cursor=cursor)
    return Page(items=[_product_read(p) for p in rows], nextCursor=nxt)


@router.get("/products/{productId}", response_model=ProductRead)
async def get_product(
    productId: str,
    _: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = (
        await session.execute(select(Product).where(Product.public_id == productId))
    ).scalar_one_or_none()
    if p is None or p.availability == "hidden":
        raise not_found("Product not found")
    return _product_read(p)


@router.post("/promotions/apply", response_model=PromoApplicationRead)
async def apply_promo(
    body: ApplyPromoRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    product = (
        await session.execute(select(Product).where(Product.public_id == body.productId))
    ).scalar_one_or_none()
    if product is None:
        raise not_found("Product not found")
    promo, discount, final = await resolve_promo(
        session, customer=customer, product=product, promo_code=body.promoCode
    )
    return PromoApplicationRead(
        promotionId=promo.public_id,
        description=promo.description,
        originalPrice=product.price,
        discountAmount=discount,
        finalPrice=final,
        currency=product.currency,
    )


@router.post(
    "/purchases", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED
)
async def create_purchase(
    body: CreatePurchaseRequest,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: IdempotencyKey = None,
):
    product = (
        await session.execute(select(Product).where(Product.public_id == body.productId))
    ).scalar_one_or_none()
    if product is None or product.availability != "available":
        raise not_found("Product not available")

    promo = None
    discount = Decimal("0.00")
    final = product.price
    if body.promoCode:
        promo, discount, final = await resolve_promo(
            session, customer=customer, product=product, promo_code=body.promoCode
        )

    account = (
        await session.execute(select(Account).where(Account.customer_id == customer.id))
    ).scalar_one()
    balance = (
        await session.execute(select(Balance).where(Balance.account_id == account.id))
    ).scalar_one()
    if balance.amount < final:
        raise conflict(
            ErrorCode.INSUFFICIENT_BALANCE,
            "Insufficient balance",
            shortfall=str(final - balance.amount),
            currency=product.currency,
        )

    # Debit wallet
    balance.amount = balance.amount - final

    # Create purchase (provisioning simulated to "active")
    purchase = Purchase(
        public_id=await next_purchase_id(session),
        customer_id=customer.id,
        product_id=product.id,
        promotion_id=promo.id if promo else None,
        status="confirmed",
        original_price=product.price,
        final_price=final,
        currency=product.currency,
        provisioning_status="active",
        provisioning_activated_at=datetime.now(UTC),
    )
    session.add(purchase)
    await session.flush()

    # Bump coupon usage if any
    if body.promoCode:
        coupon = (
            await session.execute(select(Coupon).where(Coupon.code == body.promoCode))
        ).scalar_one_or_none()
        if coupon is not None:
            coupon.usage_count += 1

    # Transaction row
    session.add(
        Transaction(
            public_id=await next_transaction_id(session),
            account_id=account.id,
            type="purchase",
            amount=-final,
            currency=product.currency,
            balance_after=balance.amount,
            related_purchase_id=purchase.id,
        )
    )

    # Phase 2 — accrue loyalty points before the audit (so the push body could include
    # the new tier if we wanted to surface it in future iterations).
    try:
        from app.services.loyalty import accrue_for_purchase

        await accrue_for_purchase(session, customer=customer, purchase=purchase)
    except Exception as exc:
        import logging
        logging.getLogger("vulnmno.shop").warning("loyalty accrual failed: %s", exc)

    await write_audit(
        session,
        event_type="PURCHASE_COMPLETED",
        actor_id=customer.public_id,
        target_type="purchase",
        target_id=purchase.public_id,
        payload={
            "productId": product.public_id,
            "finalPrice": str(final),
            "promotionId": promo.public_id if promo else None,
        },
    )
    return _purchase_read(purchase, customer, product)


@router.get("/purchases", response_model=Page[PurchaseRead])
async def list_purchases(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    status_q: str | None = Query(default=None, alias="status"),
):
    stmt = select(Purchase).where(Purchase.customer_id == customer.id)
    if status_q:
        stmt = stmt.where(Purchase.status == status_q)
    rows, nxt = await paginate(session, stmt, id_column=Purchase.id, limit=limit, cursor=cursor)
    items: list[PurchaseRead] = []
    for p in rows:
        prod = (
            await session.execute(select(Product).where(Product.id == p.product_id))
        ).scalar_one()
        items.append(_purchase_read(p, customer, prod))
    return Page(items=items, nextCursor=nxt)


@router.get("/purchases/{purchaseId}", response_model=PurchaseRead)
async def get_purchase(
    purchaseId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = (
        await session.execute(
            select(Purchase).where(
                Purchase.public_id == purchaseId, Purchase.customer_id == customer.id
            )
        )
    ).scalar_one_or_none()
    if p is None:
        raise not_found("Purchase not found")
    prod = (
        await session.execute(select(Product).where(Product.id == p.product_id))
    ).scalar_one()
    return _purchase_read(p, customer, prod)


@router.post("/purchases/{purchaseId}/cancel", response_model=PurchaseRead)
async def cancel_purchase(
    purchaseId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    p = (
        await session.execute(
            select(Purchase).where(
                Purchase.public_id == purchaseId, Purchase.customer_id == customer.id
            )
        )
    ).scalar_one_or_none()
    if p is None:
        raise not_found("Purchase not found")
    if p.status != "confirmed" or p.provisioning_status == "active":
        raise conflict(ErrorCode.CONFLICT, "Purchase no longer cancellable")
    p.status = "cancelled"

    account = (
        await session.execute(select(Account).where(Account.customer_id == customer.id))
    ).scalar_one()
    balance = (
        await session.execute(select(Balance).where(Balance.account_id == account.id))
    ).scalar_one()
    balance.amount = balance.amount + p.final_price
    session.add(
        Transaction(
            public_id=await next_transaction_id(session),
            account_id=account.id,
            type="refund",
            amount=p.final_price,
            currency=p.currency,
            balance_after=balance.amount,
            related_purchase_id=p.id,
        )
    )
    prod = (
        await session.execute(select(Product).where(Product.id == p.product_id))
    ).scalar_one()
    return _purchase_read(p, customer, prod)
