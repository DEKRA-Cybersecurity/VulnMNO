"""ORM model registry. Importing this module loads every model into Base.metadata."""

from .account import Account, Balance
from .admin import AdminUser
from .audit import AuditEvent
from .auth_tokens import IdempotencyKey, OtpChallenge, PasswordReset, RefreshToken
from .base import Base
from .customer import Customer, CustomerService
from .device import CustomerDevice
from .invoice import Invoice, InvoiceLineItem
from .line import MobileLine, SIMProfile
from .loyalty import LoyaltyAccount, LoyaltyTier, LoyaltyTransaction
from .notification import DeviceToken, Notification
from .plan import Plan, PlanChange
from .product import Product
from .promo import Coupon, Promotion
from .purchase import Purchase, Refund
from .support import SupportTicket, TicketAttachment, TicketMessage
from .transaction import Transaction
from .usage import UsageRecord

__all__ = [
    "Account",
    "AdminUser",
    "AuditEvent",
    "Balance",
    "Base",
    "Coupon",
    "Customer",
    "CustomerDevice",
    "CustomerService",
    "DeviceToken",
    "IdempotencyKey",
    "Invoice",
    "InvoiceLineItem",
    "LoyaltyAccount",
    "LoyaltyTier",
    "LoyaltyTransaction",
    "MobileLine",
    "Notification",
    "OtpChallenge",
    "PasswordReset",
    "Plan",
    "PlanChange",
    "Product",
    "Promotion",
    "Purchase",
    "Refund",
    "RefreshToken",
    "SIMProfile",
    "SupportTicket",
    "TicketAttachment",
    "TicketMessage",
    "Transaction",
    "UsageRecord",
]
