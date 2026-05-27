from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SoftDeleteMixin, TimestampMixin


class AdminUser(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "admin_users"
    __table_args__ = (Index("ix_admin_users_username", "username"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum(
            "support_agent",
            "billing_operator",
            "product_manager",
            "ops_admin",
            "security_analyst",
            "supplier_admin",
            name="admin_role",
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "deactivated", name="admin_status"),
        nullable=False,
        default="active",
    )

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
