from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Date,
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

if TYPE_CHECKING:
    from .customer import Customer


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    monthly_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    data_limit_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # -1 = unlimited
    voice_limit_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sms_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    category: Mapped[str] = mapped_column(
        Enum(
            "prepaid",
            "postpaid",
            "hybrid",
            "business",
            "student",
            "family",
            name="plan_category",
        ),
        nullable=False,
    )
    eligibility_rules: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    available_services: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class PlanChange(Base, TimestampMixin):
    __tablename__ = "plan_changes"
    __table_args__ = (
        Index("ix_plan_changes_customer_id", "customer_id"),
        Index("ix_plan_changes_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=True,
    )
    to_plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
    )

    mode: Mapped[str] = mapped_column(
        Enum("immediate", "scheduled", name="plan_change_mode"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("applied", "pending", "cancelled", name="plan_change_status"),
        nullable=False,
        default="pending",
    )
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped["Customer"] = relationship()
    from_plan: Mapped["Plan | None"] = relationship(foreign_keys=[from_plan_id])
    to_plan: Mapped["Plan"] = relationship(foreign_keys=[to_plan_id])
