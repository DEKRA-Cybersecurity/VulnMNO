# Gateway adapter drivers

## Scope

Each external integration is modeled as a Python `Protocol` (PEP 544) with two drivers: a `dev` driver that preserves Phase-1 behavior (no external calls) and a `real` driver that calls the actual service. Driver selection happens at import time from env-bound `Settings`.

| Integration | Protocol | Dev driver (default) | Real driver | Env switch |
| --- | --- | --- | --- | --- |
| Payment gateway | `app.gateways.payment.PaymentGateway` | `DevPaymentGateway` (always succeeds, `gateway_charge_id="dev_<uuid>"`) | `StripePaymentGateway` (httpx → Stripe sandbox; idempotency-key forwarded; PAYMENT_DECLINED mapping) | `VULNMNO_PAYMENT_DRIVER=stripe` + `VULNMNO_STRIPE_SECRET_KEY=...` |
| Provisioning | `app.gateways.provisioning.ProvisioningClient` | `DevProvisioning` (instant `active`) | `HttpProvisioning` (POST to mock service; 4xx permanent, 5xx transient) | `VULNMNO_PROVISIONING_DRIVER=http` + `VULNMNO_PROVISIONING_URL=...` |
| Push delivery | `app.push.fcm.PushDelivery` | `DevPush` (logs only) | `FcmPush` (firebase-admin SDK) | `VULNMNO_PUSH_DRIVER=fcm` + `VULNMNO_FCM_CREDENTIALS_PATH=/path/to/service-account.json` |

## Factories

`app/gateways/__init__.py` and `app/push/__init__.py` each expose a `get_*()` factory that reads `Settings`, instantiates the chosen driver, caches it (`@lru_cache`), and returns it. Configuration errors (e.g. `stripe` driver with empty key) degrade gracefully to the `dev` driver with a warning log; the app continues to boot.

## Where adapters are wired

| Adapter | Consumed by |
| --- | --- |
| PaymentGateway | `app/gateways/__init__.py::get_payment_gateway()` — directly available to top-up and purchase services (Stage 13 wires the actual `Depends` in routers if Stripe is enabled). For Phase 2's `dev` default, Phase 1's existing in-process wallet logic still runs unchanged. |
| ProvisioningClient | `app/gateways/__init__.py::get_provisioning_client()` — purchase confirmation calls this in async background when `provisioning_driver=http`. Dev default = current Phase-1 in-line activation. |
| PushDelivery | `app/push/audit_hook.py::maybe_send_push` — invoked from `app/services/audit.py::write_audit` after every audit event, dispatched only for customer-facing types (`PURCHASE_COMPLETED`, `PLAN_CHANGE`, `BALANCE_LOW`, `REFUND_APPROVED`). Respects `notification_preferences.push`. |

## Hook contract for audit-driven push

`audit_hook._DISPATCH` maps event type → notification spec:

```
PURCHASE_COMPLETED → channel=push, message_type=purchase_confirmation, title="Purchase confirmed"
PLAN_CHANGE        → channel=push, message_type=plan_change,           title="Plan updated"
BALANCE_LOW        → channel=push, message_type=low_balance,           title="Wallet running low"
REFUND_APPROVED    → channel=push, message_type=support_update,        title="Refund approved"
```

Every dispatched push writes a `Notification` row with `delivery_status ∈ {queued, sent, failed, skipped}` and `delivered_at` timestamp on success. `provider_message_id` stores the FCM message id (real) or `dev_<hex>` (dev).

## Verification (runtime)

With default `dev` drivers, the full Phase-1 smoke (`scripts/smoke_api.sh`) continues to pass without regressions. The notification fan-out from `PURCHASE_COMPLETED` is observable by querying `notifications` after a purchase smoke:

```bash
sqlite3 dev.db "SELECT public_id, message_type, delivery_status FROM notifications ORDER BY id DESC LIMIT 5"
```

Expected: one row per purchase with `delivery_status='sent'` (DevPush always succeeds).
