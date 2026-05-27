from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .common import ApiModel


class TicketAuthor(ApiModel):
    role: Literal["customer", "agent", "system"]
    displayName: str


class TicketMessageRead(ApiModel):
    messageId: str
    ticketId: str
    author: TicketAuthor
    body: str
    createdAt: datetime


class TicketAttachmentRead(ApiModel):
    attachmentId: str
    ticketId: str
    filename: str
    sizeBytes: int = Field(le=10 * 1024 * 1024)
    contentType: str
    uploadedAt: datetime


class TicketSummaryRead(ApiModel):
    ticketId: str
    customerId: str
    topic: Literal["Billing", "Plan", "Technical", "Purchase", "Other"]
    status: Literal["open", "pending", "closed"]
    createdAt: datetime
    lastUpdatedAt: datetime


class TicketRead(TicketSummaryRead):
    description: str
    messages: list[TicketMessageRead]
    attachments: list[TicketAttachmentRead] = []


class CreateTicketRequest(ApiModel):
    topic: Literal["Billing", "Plan", "Technical", "Purchase", "Other"]
    description: str = Field(min_length=5, max_length=4000)


class CreateMessageRequest(ApiModel):
    body: str = Field(min_length=1, max_length=4000)
