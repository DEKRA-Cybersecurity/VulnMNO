from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .common import ApiModel


class NotificationRead(ApiModel):
    notificationId: str
    customerId: str
    channel: Literal["push", "sms", "email", "in_app"]
    messageType: Literal[
        "purchase_confirmation",
        "balance_update",
        "plan_change",
        "low_balance",
        "promotion",
        "security",
        "support_update",
    ]
    title: str
    body: str
    createdAt: datetime
    readAt: datetime | None = None


class NotificationPreferences(ApiModel):
    push: bool
    sms: bool
    email: bool
    inApp: bool


class NotificationPreferencesUpdate(ApiModel):
    push: bool | None = None
    sms: bool | None = None
    email: bool | None = None
    inApp: bool | None = None


class DeviceTokenRegister(ApiModel):
    token: str = Field(min_length=10, max_length=4096)
    platform: Literal["android"]
    appVersion: str | None = None
