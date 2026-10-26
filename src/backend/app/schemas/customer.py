from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from .common import ApiModel


class Address(ApiModel):
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    postalCode: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)


class CustomerRead(ApiModel):
    customerId: str
    name: str
    email: str | None = None
    primaryMsisdn: str
    accountType: Literal["prepaid", "postpaid", "hybrid"]
    status: Literal["active", "suspended", "closed"]
    loyaltyTier: Literal["bronze", "silver", "gold", "platinum"]
    billingAddress: Address | None = None
    notificationPreferences: "NotificationPreferences | None" = None


class ContactDetailsUpdate(ApiModel):
    email: str | None = None
    billingAddress: Address | None = None
    notificationPreferences: "NotificationPreferencesUpdate | None" = None
    # API3 training lab (OWASP API Security Top 10) — see
    # src/docs/vulns/api/API3-Broken-Object-Property-Level-Authorization.md.
    # A business-controlled property wired into the self-service contact
    # details write path with no authorization check gating it.
    loyaltyTier: Literal["bronze", "silver", "gold", "platinum"] | None = None


class MobileLineRead(ApiModel):
    lineId: str
    msisdn: str
    customerId: str
    planId: str | None = None
    simId: str | None = None
    status: Literal["active", "suspended", "terminated"]
    activatedAt: datetime | None = None


class SimProfileRead(ApiModel):
    simId: str
    iccid: str
    imsiAlias: str
    type: Literal["physical", "esim"]
    status: Literal["active", "suspended", "swapped"]
    activationDate: date


class SimSwapRequest(ApiModel):
    newSimType: Literal["physical", "esim"]
    reason: str | None = Field(default=None, max_length=200)


class SimSwapResult(ApiModel):
    oldSim: SimProfileRead
    newSim: SimProfileRead


from .notification import NotificationPreferences, NotificationPreferencesUpdate  # noqa: E402

CustomerRead.model_rebuild()
ContactDetailsUpdate.model_rebuild()
