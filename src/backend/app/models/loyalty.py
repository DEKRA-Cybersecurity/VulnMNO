from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class LoyaltyTier(Base, TimestampMixin):
    __tablename__ = "loyalty_tiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        Enum("bronze", "silver", "gold", "platinum", name="loyalty_tier_name"),
        unique=True,
        nullable=False,
    )
    threshold_lifetime_points: Mapped[int] = mapped_column(Integer, nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.00"))


class LoyaltyAccount(Base, TimestampMixin):
    __tablename__ = "loyalty_accounts"
    __table_args__ = (Index("ix_loyalty_accounts_customer_id", "customer_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lifetime_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tier: Mapped[str] = mapped_column(
        Enum("bronze", "silver", "gold", "platinum", name="loyalty_acct_tier"),
        nullable=False,
        default="bronze",
    )

    transactions: Mapped[list["LoyaltyTransaction"]] = relationship(
        back_populates="account",
        order_by="LoyaltyTransaction.timestamp.desc()",
    )


class LoyaltyTransaction(Base, TimestampMixin):
    __tablename__ = "loyalty_transactions"
    __table_args__ = (
        Index("ix_loyalty_tx_account_id_ts", "account_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    account_id: Mapped[int] = mapped_column(
        ForeignKey("loyalty_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(
        Enum("purchase", "tier_bonus", "manual_adjust", "expiration", name="loyalty_tx_reason"),
        nullable=False,
    )
    related_purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchases.id", ondelete="SET NULL"),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    account: Mapped["LoyaltyAccount"] = relationship(back_populates="transactions")
