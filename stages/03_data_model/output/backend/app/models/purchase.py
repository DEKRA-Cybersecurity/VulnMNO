from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .customer import Customer
    from .product import Product
    from .promo import Promotion


class Purchase(Base, TimestampMixin):
    __tablename__ = "purchases"
    __table_args__ = (
        Index("ix_purchases_customer_id_created_at", "customer_id", "created_at"),
        Index("ix_purchases_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    promotion_id: Mapped[int | None] = mapped_column(
        ForeignKey("promotions.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        Enum("confirmed", "cancelled", "failed", name="purchase_status"),
        nullable=False,
    )
    original_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    final_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    provisioning_status: Mapped[str] = mapped_column(
        Enum("pending", "active", "failed", name="provisioning_status"),
        nullable=False,
        default="pending",
    )
    provisioning_activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer: Mapped["Customer"] = relationship()
    product: Mapped["Product"] = relationship()
    promotion: Mapped["Promotion | None"] = relationship()


class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"
    __table_args__ = (Index("ix_refunds_customer_id", "customer_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(
        Enum("purchase", "invoice", name="refund_target_type"),
        nullable=False,
    )
    target_public_id: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", name="refund_status"),
        nullable=False,
        default="pending",
    )
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("support_tickets.id", ondelete="SET NULL"),
        nullable=True,
    )
