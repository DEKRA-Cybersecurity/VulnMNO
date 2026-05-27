from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .customer import Customer
    from .plan import Plan


class SIMProfile(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sim_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    iccid: Mapped[str] = mapped_column(String(22), unique=True, nullable=False)
    imsi_alias: Mapped[str] = mapped_column(String(32), nullable=False)
    sim_type: Mapped[str] = mapped_column(
        Enum("physical", "esim", name="sim_type"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", "swapped", name="sim_status"),
        nullable=False,
        default="active",
    )
    activation_date: Mapped[date] = mapped_column(Date, nullable=False)

    line: Mapped["MobileLine"] = relationship(back_populates="sim", uselist=False)


class MobileLine(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "mobile_lines"
    __table_args__ = (
        Index("ix_mobile_lines_customer_id", "customer_id"),
        Index("ix_mobile_lines_plan_id", "plan_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    msisdn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    sim_id: Mapped[int | None] = mapped_column(
        ForeignKey("sim_profiles.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", "terminated", name="line_status"),
        nullable=False,
        default="active",
    )
    activated_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="lines")
    plan: Mapped["Plan | None"] = relationship()
    sim: Mapped["SIMProfile | None"] = relationship(back_populates="line")
