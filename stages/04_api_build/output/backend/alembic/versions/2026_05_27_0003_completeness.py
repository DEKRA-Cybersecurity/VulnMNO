"""completeness passes — customer_devices table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-27 14:00:00.000000+00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column(
            "platform",
            sa.Enum("android", "ios", "web", name="customer_device_platform"),
            nullable=False,
        ),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("app_version", sa.String(length=40), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trusted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_id", "device_id", name="uq_customer_devices_customer_device"
        ),
    )
    op.create_index(
        "ix_customer_devices_customer_id",
        "customer_devices",
        ["customer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_customer_devices_customer_id", table_name="customer_devices")
    op.drop_table("customer_devices")
    sa.Enum(name="customer_device_platform").drop(op.get_bind(), checkfirst=False)
