from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, condecimal

from .common import ApiModel, Money

Volume = Annotated[Decimal, condecimal(max_digits=12, decimal_places=3)]


class UsageRecordRead(ApiModel):
    usageId: str
    lineId: str
    type: Literal["call", "sms", "data", "roaming"]
    direction: Literal["incoming", "outgoing"] | None = None
    destination: str | None = None
    startedAt: datetime
    durationSeconds: int | None = None
    volumeMegabytes: Volume | None = None
    country: str | None = None
    networkType: str | None = None
    roaming: bool = False
    cost: Money
    currency: Literal["EUR"] = "EUR"
