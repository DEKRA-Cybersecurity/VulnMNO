from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .account import Account
    from .line import MobileLine
    from .notification import DeviceToken, Notification
    from .support import SupportTicket


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    primary_msisdn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    account_type: Mapped[str] = mapped_column(
        Enum("prepaid", "postpaid", "hybrid", name="account_type"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", "closed", name="customer_status"),
        nullable=False,
        default="active",
    )
    loyalty_tier: Mapped[str] = mapped_column(
        Enum("bronze", "silver", "gold", "platinum", name="loyalty_tier"),
        nullable=False,
        default="bronze",
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    otp_enrolled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    otp_fixed_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    billing_address: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notification_preferences: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {"push": True, "sms": True, "email": True, "inApp": True},
    )

    account: Mapped["Account"] = relationship(back_populates="customer", uselist=False)
    lines: Mapped[list["MobileLine"]] = relationship(back_populates="customer")
    tickets: Mapped[list["SupportTicket"]] = relationship(back_populates="customer")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="customer")
    device_tokens: Mapped[list["DeviceToken"]] = relationship(back_populates="customer")
    services: Mapped[list["CustomerService"]] = relationship(back_populates="customer")


class CustomerService(Base, TimestampMixin):
    __tablename__ = "customer_services"
    __table_args__ = (
        Index("ix_customer_services_customer_id", "customer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_id: Mapped[str] = mapped_column(String(64), nullable=False)

    customer: Mapped["Customer"] = relationship(back_populates="services")
