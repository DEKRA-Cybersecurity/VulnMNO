# End-to-end test cases — Phase 2

Phase-1 cases (`INT-001…INT-010`) remain in [stages/07_integration/output/e2e-cases.md](../../07_integration/output/e2e-cases.md). Phase 2 adds `INT-200…` covering admin portal, loyalty, i18n, rate limiting, and integration adapters.

## Inputs consumed

- `../07_integration/output/e2e-cases.md`
- `../11_admin_portal_build/output/admin-screens-built.md`
- `../12_integrations_and_ops/output/*.md`

## Findings

| ID | Area | Steps (curl / SCR / ADM / AEP) | Expected | Seed data |
| --- | --- | --- | --- | --- |
| INT-200 | Admin login + dashboard | GET /admin/login → grab CSRF → POST /admin/login (ops/admin1234) → GET /admin/ | 303 to `/admin/`, dashboard renders KPI tiles + recent audit feed; `AuditEvent ADMIN_LOGIN_SUCCESS` written. | seed_phase2 admin users. |
| INT-201 | Admin balance adjust (billing role) | log in as billing/admin1234 → POST /admin/customers/CUST-10001/balance-adjust amount=+5.00 reason≥10 | 200, HTML fragment shows updated balance; `Transaction(type=adjustment)` exists; `ADMIN_BALANCE_ADJUSTMENT` audited. | Alice. |
| INT-202 | Admin RBAC denial | log in as support/admin1234 → POST same balance-adjust | 403 ADMIN_FORBIDDEN; no transaction created. | Alice. |
| INT-203 | Refund approval (wallet credited) | Customer Alice POSTs refund via /api/accounts/me/refunds for an existing purchase → admin (billing) approves via /admin/refunds/{id}/approve | Refund.status=approved; new `Transaction(type=refund, amount=+X)` credits Alice's wallet; ticket auto-closed; `ADMIN_REFUND_APPROVED` audited. | Alice + a confirmed PUR-… purchase. |
| INT-204 | Agent ticket reply | Alice creates a ticket → support agent (support/admin1234) logs into admin → opens `/admin/tickets/{id}` → posts agent-reply | New `TicketMessage(author_role='agent', author_display_name=<admin>)`; ticket `last_updated_at` advances; `ADMIN_TICKET_REPLY` audited. | Alice. |
| INT-205 | Plan create + archive (product role) | product/admin1234 logs in → POSTs /admin/plans/new with new public_id → POSTs /admin/plans/{id}/archive | Plan row exists; `eligibility_rules.archived=true`; both events audited. | none |
| INT-206 | Coupon batch generate | product/admin1234 → POST /admin/promotions/PROMO-SUMMER-2026/coupons/generate count=25 | 25 new `Coupon` rows with unique codes; `ADMIN_COUPONS_GENERATED` audited. | seed promo. |
| INT-207 | Loyalty accrual visible to mobile | Customer Alice (silver, 0 pts) buys DATA-10GB-7D with SUMMER20 → GET /api/loyalty/account | response shows `points=10, tier=silver, multiplier=1.20`. | Alice. |
| INT-208 | Loyalty history endpoint | Same as INT-207 + GET /api/loyalty/transactions | response includes one row `delta=10, reason='purchase', relatedPurchaseId=PUR-…`. | Alice. |
| INT-209 | i18n Spanish error | POST /api/auth/login with `Accept-Language: es` + wrong password | 401 INVALID_CREDENTIALS, `error.message = "Número o contraseña incorrectos."` | seed. |
| INT-210 | i18n English error | Same request with `Accept-Language: en` | 401 INVALID_CREDENTIALS, `error.message = "Wrong phone number or password."` | seed. |
| INT-211 | Rate limit hits 429 | POST /api/auth/login 7× in under a minute with random msisdn + wrong password | First 5 attempts return 401; subsequent attempts return 429 with `RATE_LIMITED` and `Retry-After: 60`. | none. |
| INT-212 | Audit log viewer filters | log in as security/admin1234 → GET /admin/audit?event_type=ADMIN_BALANCE_ADJUSTMENT | HTML table shows only matching rows. | needs INT-201 first. |
| INT-213 | Admin user lifecycle (ops role) | ops → POST /admin/staff/new (new admin) → POST /admin/staff/{id}/deactivate | New `AdminUser` exists with status=active then deactivated; both events audited. | none. |

## How to run (Phase 2)

### Headless admin smoke

```bash
( cd stages/04_api_build/output/backend && uvicorn app.main:app --port 8000 ) &
sleep 2
bash stages/13_phase2_integration/output/scripts/smoke_admin.sh
```

`smoke_admin.sh` exits non-zero on the first failure. Covers INT-200, INT-201, INT-202, INT-207, INT-208, INT-209/210, INT-211.

### Full mobile + admin pass

Run the Phase-1 backend smoke (still green — drivers default to `dev`):

```bash
bash stages/07_integration/output/scripts/smoke_api.sh
```

Then the Phase-2 admin smoke. Then walk through the extended mobile checklist:

```bash
# stages/13_phase2_integration/output/scripts/smoke_mobile.md (extends Phase-1)
```

### Prod-like (Postgres + provisioning mock)

```bash
docker compose -f stages/13_phase2_integration/output/docker-compose.yml up --build
```

This brings up: Postgres 16 + backend (Phase 2) + provisioning-mock. Stripe sandbox and FCM remain optional — exercise them by setting the relevant env vars on the `backend` service.

## Open questions

None remaining.
