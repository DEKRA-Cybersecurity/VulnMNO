# Stage 12 — Integrations & ops

Replace Phase-1 stubs with real adapters, add rate limiting, i18n, loyalty engine, refund workflow side effects, and the campaign scheduler. All driven by env settings — the default `dev` drivers preserve Phase 1 behavior.

## Inputs

**Layer 4 (working):**
- `../09_phase2_contract/output/adapter-interfaces.md` (PaymentGateway / ProvisioningClient / PushDelivery)
- `../09_phase2_contract/output/loyalty-endpoints.md`
- `../08_phase2_requirements/output/backlog.md` (REQ-270…REQ-331)
- `../10_phase2_data_model/output/entities-delta.md`

**Layer 3 (reference):**
- `../../_config/code-style.md`

## Process

1. **`app/gateways/`** subpackage: `payment.py`, `provisioning.py`, `__init__.py` (factory + FastAPI Depends).
2. **`app/push/`** subpackage: `fcm.py`, `__init__.py`, `audit_hook.py` (writes Notification + delivery_status).
3. **Wire payment gateway** into `app/routers/accounts.py::topup` and `shop.py::create_purchase`. Persist `gateway_charge_id` on `Transaction`. Map `PAYMENT_DECLINED`.
4. **Wire provisioning** into `create_purchase` post-confirm. Background asyncio retry on transient failures.
5. **Wire push hook** into `app/services/audit.py::write_audit` — after writing an audit event of a customer-facing type, queue a `Notification` and call the push adapter. Respect `notification_preferences.push`.
6. **`app/services/loyalty.py`** — hook in `create_purchase`: compute points = floor(final_price × tier.multiplier), insert `LoyaltyTransaction`, recompute balance and tier.
7. **`app/services/refund.py`** — admin refund approve calls this: creates `Transaction(type=refund, amount=+X)` crediting the wallet, marks `Refund.status='approved'`, audits.
8. **`app/services/campaign_scheduler.py`** — lifespan-scheduled coroutine that hourly opens promotions whose `starts_at` arrived and closes ones whose `ends_at` passed.
9. **`app/routers/loyalty.py`** — `EP-090 GET /api/loyalty/account` + `EP-091 GET /api/loyalty/transactions` for the mobile app.
10. **`app/i18n.py`** — locale-aware message catalog (Accept-Language header). YAML at `app/i18n_catalog.yaml` with es/en.
11. **slowapi rate limiting** — `Limiter(key_func=customer_or_ip)` in `app/main.py`. Bands per spec: `/api/auth/*` 5/min/IP; purchases + topup 10/min/customer; admin login 5/min/IP; default 60/min/customer.
12. **Android i18n** — `app/src/main/res/values-es/strings.xml` mirroring `values/strings.xml`.

## Outputs

Code committed in-place into `04_api_build/output/backend/` and `06_mobile_build/output/android/`.

Stage-level outputs (`output/`):
- `adapter-drivers.md` — table of drivers + env switches.
- `rate-limit-bands.md` — endpoint → limit table.
- `i18n-keys.md` — message keys catalog.
- `loyalty-rules.md` — tier thresholds + multipliers + accrual formula.
- `settings-delta.md` — env vars added in Phase 2.
