from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .common import ApiModel, Money


class BalanceRead(ApiModel):
    accountId: str
    balance: Money
    currency: Literal["EUR"] = "EUR"
    lastUpdated: datetime


class TransactionRead(ApiModel):
    transactionId: str
    accountId: str
    type: Literal["topup", "purchase", "refund", "adjustment", "charge"]
    amount: Money
    currency: Literal["EUR"] = "EUR"
    balanceAfter: Money
    relatedPurchaseId: str | None = None
    relatedInvoiceId: str | None = None
    timestamp: datetime


class TopupRequest(ApiModel):
    amount: Money = Field(ge=1, le=500)
    currency: Literal["EUR"] = "EUR"


class InvoiceLineItem(ApiModel):
    description: str
    amount: Money
    currency: Literal["EUR"] = "EUR"
    relatedProductId: str | None = None
    relatedPlanId: str | None = None


class InvoiceSummaryRead(ApiModel):
    invoiceId: str
    accountId: str
    period: str
    totalAmount: Money
    currency: Literal["EUR"] = "EUR"
    status: Literal["draft", "issued", "paid", "overdue", "void"]
    issuedAt: datetime


class InvoiceRead(InvoiceSummaryRead):
    lineItems: list[InvoiceLineItem]


class RefundRequest(ApiModel):
    targetType: Literal["purchase", "invoice"]
    targetId: str
    reason: str = Field(min_length=5, max_length=500)


class RefundCreated(ApiModel):
    refundId: str
    status: Literal["pending"] = "pending"
    ticketId: str
