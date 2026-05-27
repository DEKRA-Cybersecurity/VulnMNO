# Implementation checklist

Implement endpoint groups in this order. Each group's DoD is "tests green + sample request returns spec-compliant payload".

## Order

1. **auth** (`/api/auth/*`) — login, refresh, logout, OTP verify, password reset request/confirm. Establishes the auth dependency that every other router uses.
2. **customers** (`/api/customers/me*`) — profile, contact details, lines, sim-profile. Smallest surface to validate auth wiring end-to-end.
3. **accounts** (`/api/accounts/me/*`) — balance, transactions, top-up, invoices (list, detail, download), refunds.
4. **shop** (`/api/shop/*`) — products list/detail, promotions apply, purchases create/list/get/cancel.
5. **plans** (`/api/plans/*`) — current, available, change, cancel change, services add/remove.
6. **usage** (`/api/usage/*`) — calls, sms, data, roaming, export.
7. **support** (`/api/support/*`) — tickets create/list/get, messages, attachments, close.
8. **notifications** (`/api/notifications/*`) — list, preferences, device-token (stub delivery).

## Per-group definition of done

For each group:

- [ ] Pydantic schemas mirror `openapi.yaml` exactly (run `app.openapi()` and diff).
- [ ] Router file uses the standard auth dependency (`Depends(get_current_customer)`) for protected endpoints.
- [ ] Business logic lives in `app/services/<group>.py`, not in the router.
- [ ] Error responses use the single error envelope and codes from `error-codes.md`.
- [ ] At least one pytest per endpoint: happy path. At least one negative test per group: auth failure or domain error.
- [ ] Audit events written for the actions listed in stage 04 CONTEXT.md step 4.

## Cross-cutting

- **Identity scoping rule.** Always resolve `me` from `current_customer.public_id`. Never trust a path or query argument named `customerId`.
- **Idempotency.** Top-up, purchase create and plan change accept an optional `Idempotency-Key` header. Store-and-replay for 24h. If absent, generate one server-side per request.
- **Rate limits.** Out of phase 1 scope. Document the seams (decorator hook) but do not enforce.
- **CORS.** Allow the Android debug origin (`http://10.0.2.2`) and the configured LAN dev origin in `dev`. In `prod-like`, allow nothing by default.
- **Logging.** Structured JSON in `prod-like` (one line per request). Plain text in `dev`. Never log token values, OTPs or passwords.
- **Provisioning + payment gateway.** Simulate. Log the intent to the audit service and return a deterministic success unless the seed data sets up a failure scenario.

## Local run

`uvicorn app.main:app --reload --port 8000` from `output/backend/`. SQLite DB at `dev.db` is created and seeded on first boot via FastAPI lifespan. Re-running is safe (seed is idempotent).
