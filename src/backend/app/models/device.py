from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .customer import Customer


class CustomerDevice(Base, TimestampMixin):
    """Logical device record (separate from FCM push tokens in DeviceToken).

    Tracks every (customer, device-id) pair the client announces. Used to feed
    LOGIN_SUCCESS audit events with a stable `deviceId` (docs §12.1) and to
    distinguish first-time vs. recurring devices (docs §10.1, §13.1).
    """

    __tablename__ = "customer_devices"
    __table_args__ = (
        UniqueConstraint("customer_id", "device_id", name="uq_customer_devices_customer_device"),
        Index("ix_customer_devices_customer_id", "customer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    platform: Mapped[str] = mapped_column(
        Enum("android", "ios", "web", name="customer_device_platform"),
        nullable=False,
    )
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trusted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    customer: Mapped["Customer"] = relationship(back_populates="devices")
