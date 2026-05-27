from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from .common import ApiModel, Money


class PlanRead(ApiModel):
    planId: str
    name: str
    description: str | None = None
    monthlyPrice: Money
    currency: Literal["EUR"] = "EUR"
    dataLimit: int
    voiceLimit: int
    smsLimit: int = 0
    category: Literal["prepaid", "postpaid", "hybrid", "business", "student", "family"]
    activeServices: list[str] = Field(default_factory=list)
    validFrom: datetime | None = None


class PlanChangeRequest(ApiModel):
    planId: str
    mode: Literal["immediate", "scheduled"]
    effectiveDate: date | None = None


class PlanChangeRead(ApiModel):
    changeId: str
    customerId: str
    fromPlanId: str | None = None
    toPlanId: str
    status: Literal["applied", "pending", "cancelled"]
    mode: Literal["immediate", "scheduled"]
    effectiveDate: date | None = None
    createdAt: datetime


class ServiceToggleRequest(ApiModel):
    serviceId: str
