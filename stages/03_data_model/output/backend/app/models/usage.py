from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class UsageRecord(Base, TimestampMixin):
    __tablename__ = "usage_records"
    __table_args__ = (
        Index("ix_usage_records_line_id_started_at", "line_id", "started_at"),
        Index("ix_usage_records_type", "type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    line_id: Mapped[int] = mapped_column(
        ForeignKey("mobile_lines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        Enum("call", "sms", "data", "roaming", name="usage_type"),
        nullable=False,
    )
    direction: Mapped[str | None] = mapped_column(
        Enum("incoming", "outgoing", name="usage_direction"),
        nullable=True,
    )
    destination: Mapped[str | None] = mapped_column(String(40), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_megabytes: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    network_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    roaming: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
