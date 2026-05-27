from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Promotion(Base, TimestampMixin):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    discount_type: Mapped[str] = mapped_column(
        Enum("percent", "fixed", name="discount_type"),
        nullable=False,
    )
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    eligibility_rules: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    eligible_product_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    combinable: Mapped[bool] = mapped_column(default=False, nullable=False)

    coupons: Mapped[list["Coupon"]] = relationship(back_populates="promotion")


class Coupon(Base, TimestampMixin):
    __tablename__ = "coupons"
    __table_args__ = (Index("ix_coupons_promotion_id", "promotion_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    promotion_id: Mapped[int] = mapped_column(
        ForeignKey("promotions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "exhausted", "disabled", name="coupon_status"),
        nullable=False,
        default="active",
    )
    usage_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    promotion: Mapped["Promotion"] = relationship(back_populates="coupons")
