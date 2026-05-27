from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .common import ApiModel, Money


class ProductRead(ApiModel):
    productId: str
    name: str
    category: Literal[
        "data_bundle",
        "voice_bundle",
        "sms_bundle",
        "roaming",
        "addon",
        "accessory",
        "loyalty",
        "promo",
    ]
    description: str | None = None
    price: Money
    currency: Literal["EUR"] = "EUR"
    validityDays: int | None = None
    eligiblePlans: list[str] = Field(default_factory=list)
    featured: bool = False
    availability: Literal["available", "sold_out", "hidden"] = "available"


class ApplyPromoRequest(ApiModel):
    productId: str
    promoCode: str = Field(min_length=1, max_length=64)


class PromoApplicationRead(ApiModel):
    promotionId: str
    description: str | None = None
    originalPrice: Money
    discountAmount: Money
    finalPrice: Money = Field(ge=0)
    currency: Literal["EUR"] = "EUR"


class CreatePurchaseRequest(ApiModel):
    productId: str
    promoCode: str | None = None


class ProvisioningStatus(ApiModel):
    status: Literal["pending", "active", "failed"]
    activatedAt: datetime | None = None


class PurchaseRead(ApiModel):
    purchaseId: str
    customerId: str
    productId: str
    promotionId: str | None = None
    status: Literal["confirmed", "cancelled", "failed"]
    originalPrice: Money
    finalPrice: Money
    currency: Literal["EUR"] = "EUR"
    createdAt: datetime
    provisioning: ProvisioningStatus
