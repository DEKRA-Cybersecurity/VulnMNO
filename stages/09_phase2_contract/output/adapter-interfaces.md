# Gateway adapter interfaces

## Scope

Three external integrations modeled as Python `Protocol` classes (PEP 544). Each Protocol has a `dev` driver (preserves Phase-1 behavior, always succeeds locally) and a `real` driver (Stripe sandbox / HTTP mock / FCM). Driver selection happens at startup via env settings (Stage 12).

These are NOT OpenAPI schemas. They are abstract Python interfaces that Stage 12 implements and Stage 11's admin/router code consumes via FastAPI `Depends`.

## Inputs consumed

- `../08_phase2_requirements/output/backlog.md` (REQ-270…REQ-292 — gateway requirements).
- `../02_api_contract/output/error-codes.md` + the Phase 2 delta below.

## Findings

### Common conventions

- All adapter methods are `async def`. They never block — gateway calls use `httpx.AsyncClient`.
- All adapter methods accept an optional `ctx: GatewayContext` parameter carrying the customer ID, request id, and a logger. The default `ctx` is built from FastAPI's `Request` via a dependency.
- Failure is signaled by **returning a result type with a `success: bool` flag and an `error_code` field**, not by raising. The router layer translates failures into `AppError` (`PAYMENT_DECLINED`, `PROVISIONING_FAILED`, `PUSH_FAILED`).
- `Idempotency-Key` is forwarded by the caller — adapters do not generate or persist them; that responsibility stays in the existing `IdempotencyKey` table (Phase 1).

### PaymentGateway (GW-001)

```python
from typing import Protocol, Literal
from decimal import Decimal
from dataclasses import dataclass

@dataclass(frozen=True)
class ChargeResult:
    success: bool
    gateway_charge_id: str | None         # e.g. "ch_3OabCd…" from Stripe; None on failure
    raw_status: str                       # e.g. "succeeded", "card_declined"
    error_code: Literal[
        "ok", "card_declined", "insufficient_funds", "gateway_error", "rate_limited"
    ]
    error_message: str | None = None

class PaymentGateway(Protocol):
    name: str                              # "dev" or "stripe"

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
```

**Drivers (implemented in Stage 12):**

- `DevPaymentGateway`: `charge` always returns `success=True` with `gateway_charge_id="dev_<uuid>"`. Used in Phase-1 mode and tests. `refund` mirrors.
- `StripePaymentGateway`: httpx → `POST https://api.stripe.com/v1/charges` with `Idempotency-Key` header and `Authorization: Bearer ${STRIPE_SECRET_KEY}`. Maps Stripe errors to the `error_code` enum.

### ProvisioningClient (GW-010, GW-011)

```python
from dataclasses import dataclass
from typing import Literal, Protocol

@dataclass(frozen=True)
class ProvisionResult:
    success: bool
    provisioning_id: str | None
    raw_status: str
    error_code: Literal["ok", "transient", "permanent", "timeout"]
    error_message: str | None = None

class ProvisioningClient(Protocol):
    name: str                              # "dev" or "http"

    async def activate_bundle(
        self,
        *,
        customer_id: str,
        product_id: str,
        purchase_id: str,
    ) -> ProvisionResult: ...

    async def deactivate_bundle(
        self,
        *,
        provisioning_id: str,
        reason: str,
    ) -> ProvisionResult: ...
```

**Drivers:**

- `DevProvisioning`: returns `success=True, provisioning_id="dev_<uuid>"` synchronously. Phase-1 behavior.
- `HttpProvisioning`: `POST ${PROVISIONING_URL}/activate` with the payload. Stage 12 wraps this in a retry helper (exponential backoff 1s / 5s / 30s, after which auto-refund per REQ-281).

### PushDelivery (GW-020, GW-021)

```python
from dataclasses import dataclass
from typing import Literal, Protocol

@dataclass(frozen=True)
class SendResult:
    success: bool
    provider_message_id: str | None
    error_code: Literal[
        "ok", "no_token", "invalid_token", "rate_limited", "provider_error"
    ]
    error_message: str | None = None

class PushDelivery(Protocol):
    name: str                              # "dev" or "fcm"

    async def send(
        self,
        *,
        customer_id: str,
        notification_id: str,
        title: str,
        body: str,
        data: dict[str, str],              # FCM data-payload, all values must be strings
    ) -> SendResult: ...
```

**Drivers:**

- `DevPush`: log at INFO and return `success=True, provider_message_id="dev_<uuid>"`. Phase-1 behavior.
- `FcmPush`: uses `firebase-admin` Python SDK. Reads service-account JSON from `${VULNMNO_FCM_CREDENTIALS}`. On `messaging.UnregisteredError` returns `error_code="invalid_token"` so the caller can purge the stale `DeviceToken` row.

### Audit-event → push mapping (Stage 12 hook)

| AuditEvent type | Push? | messageType used for Notification | Title key (i18n) |
| --- | --- | --- | --- |
| `LOGIN_SUCCESS` | no (security side-channel) | — | — |
| `PURCHASE_COMPLETED` | yes | `purchase_confirmation` | `notification.purchase.title` |
| `PLAN_CHANGE` | yes | `plan_change` | `notification.plan_change.title` |
| `BALANCE_LOW` (synthetic, fired when post-purchase balance < €5) | yes | `low_balance` | `notification.low_balance.title` |
| `REFUND_APPROVED` (from admin flow) | yes | `support_update` | `notification.refund_approved.title` |
| `ADMIN_*` events | no | — | — |

The mapping lives in `app/push/audit_hook.py` (Stage 12).

## Dependency wiring (Stage 12 / FastAPI)

```python
# app/gateways/__init__.py
from typing import Annotated
from fastapi import Depends

def get_payment_gateway() -> PaymentGateway: ...
def get_provisioning_client() -> ProvisioningClient: ...
def get_push_delivery() -> PushDelivery: ...

# routers use:
async def topup(..., gw: Annotated[PaymentGateway, Depends(get_payment_gateway)]): ...
```

## Open questions

None.
