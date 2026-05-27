from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Enum, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(
        Enum(
            "data_bundle",
            "voice_bundle",
            "sms_bundle",
            "roaming",
            "addon",
            "accessory",
            "loyalty",
            "promo",
            name="product_category",
        ),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    validity_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eligible_plans: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    availability: Mapped[str] = mapped_column(
        Enum("available", "sold_out", "hidden", name="product_availability"),
        nullable=False,
        default="available",
    )
