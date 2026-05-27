"""Payment gateway adapters — dev + Stripe sandbox."""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol

import httpx

log = logging.getLogger("vulnmno.gateways.payment")

ChargeErrorCode = Literal[
    "ok", "card_declined", "insufficient_funds", "gateway_error", "rate_limited"
]


@dataclass(frozen=True)
class ChargeResult:
    success: bool
    gateway_charge_id: str | None
    raw_status: str
    error_code: ChargeErrorCode
    error_message: str | None = None


class PaymentGateway(Protocol):
    name: str

    async def charge(
        self,
        *,
        customer_id: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        description: str,
    ) -> ChargeResult: ...

    async def refund(
        self,
        *,
        charge_id: str,
        amount: Decimal,
        reason: str,
    ) -> ChargeResult: ...


class DevPaymentGateway:
    """Local-only: always succeeds. Phase-1 behavior preserved."""

    name = "dev"

    async def charge(self, **kwargs) -> ChargeResult:
        return ChargeResult(
            success=True,
            gateway_charge_id=f"dev_{secrets.token_hex(8)}",
            raw_status="succeeded",
            error_code="ok",
        )

    async def refund(self, **kwargs) -> ChargeResult:
        return ChargeResult(
            success=True,
            gateway_charge_id=f"dev_refund_{secrets.token_hex(8)}",
            raw_status="refunded",
            error_code="ok",
        )


# ----- Stripe sandbox driver -----

class StripePaymentGateway:
    name = "stripe"

    def __init__(self, *, secret_key: str, base_url: str = "https://api.stripe.com") -> None:
        self._secret = secret_key
        self._base = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=15.0)

    async def charge(
        self,
        *,
        customer_id: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        description: str,
    ) -> ChargeResult:
        # Stripe expects amount in the smallest currency unit (cents for EUR).
        cents = int((amount * Decimal("100")).to_integral_value())
        try:
            resp = await self._client.post(
                f"{self._base}/v1/charges",
                headers={
                    "Authorization": f"Bearer {self._secret}",
                    "Idempotency-Key": idempotency_key,
                },
                data={
                    "amount": cents,
                    "currency": currency.lower(),
                    "source": "tok_visa",  # sandbox test token
                    "description": description,
                    "metadata[customer_id]": customer_id,
                },
            )
        except httpx.HTTPError as exc:
            log.warning("stripe charge transport error: %s", exc)
            return ChargeResult(
                success=False, gateway_charge_id=None, raw_status="gateway_error",
                error_code="gateway_error", error_message=str(exc),
            )

        if resp.status_code in (200, 201):
            data = resp.json()
            return ChargeResult(
                success=True,
                gateway_charge_id=data.get("id"),
                raw_status=data.get("status", "succeeded"),
                error_code="ok",
            )

        try:
            err = resp.json().get("error", {})
        except Exception:
            err = {}
        code = err.get("code") or err.get("type") or "gateway_error"
        # Map a few common Stripe error codes
        mapped: ChargeErrorCode = "gateway_error"
        if code in ("card_declined", "expired_card", "incorrect_cvc"):
            mapped = "card_declined"
        elif code in ("insufficient_funds",):
            mapped = "insufficient_funds"
        elif resp.status_code == 429:
            mapped = "rate_limited"
        return ChargeResult(
            success=False,
            gateway_charge_id=err.get("charge"),
            raw_status=str(resp.status_code),
            error_code=mapped,
            error_message=err.get("message"),
        )

    async def refund(self, *, charge_id: str, amount: Decimal, reason: str) -> ChargeResult:
        cents = int((amount * Decimal("100")).to_integral_value())
        try:
            resp = await self._client.post(
                f"{self._base}/v1/refunds",
                headers={"Authorization": f"Bearer {self._secret}"},
                data={"charge": charge_id, "amount": cents, "reason": "requested_by_customer"},
            )
        except httpx.HTTPError as exc:
            return ChargeResult(False, None, "gateway_error", "gateway_error", str(exc))
        if resp.status_code in (200, 201):
            d = resp.json()
            return ChargeResult(True, d.get("id"), d.get("status", "refunded"), "ok")
        return ChargeResult(False, None, str(resp.status_code), "gateway_error", resp.text[:200])
