from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .customer import Customer
    from .transaction import Transaction


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"
    __table_args__ = (Index("ix_accounts_customer_id", "customer_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    account_type: Mapped[str] = mapped_column(
        Enum("prepaid", "postpaid", "hybrid", name="account_type_acct"),
        nullable=False,
    )
    billing_status: Mapped[str] = mapped_column(
        Enum("good_standing", "overdue", "suspended", name="billing_status"),
        nullable=False,
        default="good_standing",
    )

    customer: Mapped["Customer"] = relationship(back_populates="account")
    balance: Mapped["Balance"] = relationship(back_populates="account", uselist=False)
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Balance(Base, TimestampMixin):
    __tablename__ = "balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    account: Mapped["Account"] = relationship(back_populates="balance")
