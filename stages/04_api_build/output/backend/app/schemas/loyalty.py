from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, condecimal

from .common import ApiModel

Multiplier = Annotated[Decimal, condecimal(max_digits=4, decimal_places=2)]


class LoyaltyAccountRead(ApiModel):
    customerId: str
    points: int = Field(ge=0)
    lifetimePoints: int = Field(ge=0)
    tier: Literal["bronze", "silver", "gold", "platinum"]
    multiplier: Multiplier
    nextTier: Literal["silver", "gold", "platinum"] | None = None
    pointsToNextTier: int | None = None


class LoyaltyTransactionRead(ApiModel):
    transactionId: str
    accountId: str
    delta: int
    balanceAfter: int = Field(ge=0)
    reason: Literal["purchase", "tier_bonus", "manual_adjust", "expiration"]
    relatedPurchaseId: str | None = None
    timestamp: datetime
