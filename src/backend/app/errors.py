from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    UNAUTHENTICATED = "UNAUTHENTICATED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    OTP_INVALID = "OTP_INVALID"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    CONFLICT = "CONFLICT"
    INTERNAL = "INTERNAL"
    PROMO_INVALID = "PROMO_INVALID"
    PROMO_INELIGIBLE = "PROMO_INELIGIBLE"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    PLAN_INELIGIBLE = "PLAN_INELIGIBLE"
    PLAN_CHANGE_PENDING = "PLAN_CHANGE_PENDING"
    TICKET_CLOSED = "TICKET_CLOSED"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    # Phase 2 additions
    ADMIN_FORBIDDEN = "ADMIN_FORBIDDEN"
    ADMIN_SESSION_EXPIRED = "ADMIN_SESSION_EXPIRED"
    PAYMENT_DECLINED = "PAYMENT_DECLINED"
    PROVISIONING_FAILED = "PROVISIONING_FAILED"
    PUSH_FAILED = "PUSH_FAILED"
    LOYALTY_INSUFFICIENT_POINTS = "LOYALTY_INSUFFICIENT_POINTS"


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        http_status: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}

    def envelope(self) -> dict[str, Any]:
        body: dict[str, Any] = {"code": self.code.value, "message": self.message}
        if self.details:
            body["details"] = self.details
        return {"error": body}


def unauthenticated(message: str = "Bearer token missing or invalid") -> AppError:
    return AppError(ErrorCode.UNAUTHENTICATED, message, http_status=401)


def not_found(message: str = "Resource not found") -> AppError:
    return AppError(ErrorCode.NOT_FOUND, message, http_status=404)


def conflict(code: ErrorCode, message: str, **details: Any) -> AppError:
    return AppError(code, message, http_status=409, details=details)


def bad_request(code: ErrorCode, message: str, **details: Any) -> AppError:
    return AppError(code, message, http_status=400, details=details)
