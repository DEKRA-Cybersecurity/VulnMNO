# OWASP API Security Top 10 (2023) → VulnMNO mapping

Decision record for stage 17. All ten categories are **live** in the sense
that the weakness is really present in `src/backend` right now (confirmed by
a direct code read for every one of the ten). The six newly-introduced
categories were additionally verified by actually running the exploit
against a live instance (SQLite dev DB, seeded data) and confirming the real
response/state change — their guides under `src/docs/vulns/api/` carry a
"Verified exploitation (actual run)" section with the real captured
transcript. The four pre-existing categories (API2, API4, API6, API8) were
*not* re-run with captured output during this stage — their guides carry
illustrative `curl` commands only (bannered "Dynamic exploitation", not
"Verified exploitation"); the finding itself is still real and directly
traceable to the cited file:line, just not re-exercised live here. See the
section below for exactly which group is which.

| # | Category (2023) | Zone | Guide |
|---|---|---|---|
| API1 | Broken Object Level Authorization | `GET /api/support/tickets/by-reference/{ticketId}` | [guide](../../../src/docs/vulns/api/API1-Broken-Object-Level-Authorization.md) |
| API2 | Broken Authentication | `POST /api/auth/otp/verify`, `POST /api/auth/password-reset/confirm` | [guide](../../../src/docs/vulns/api/API2-Broken-Authentication.md) |
| API3 | Broken Object Property Level Authorization | `PUT /api/customers/me/contact-details` (`loyaltyTier`) | [guide](../../../src/docs/vulns/api/API3-Broken-Object-Property-Level-Authorization.md) |
| API4 | Unrestricted Resource Consumption | `POST /api/auth/refresh`, `GET /api/usage/export` | [guide](../../../src/docs/vulns/api/API4-Unrestricted-Resource-Consumption.md) |
| API5 | Broken Function Level Authorization | `POST /admin/refunds/{refundId}/quick-approve` | [guide](../../../src/docs/vulns/api/API5-Broken-Function-Level-Authorization.md) |
| API6 | Unrestricted Access to Sensitive Business Flows | `POST /api/shop/purchases` (promo redemption, §9.2 journey) | [guide](../../../src/docs/vulns/api/API6-Unrestricted-Access-to-Sensitive-Business-Flows.md) |
| API7 | Server Side Request Forgery | `POST /api/auth/devices` (`callbackUrl`) | [guide](../../../src/docs/vulns/api/API7-Server-Side-Request-Forgery.md) |
| API8 | Security Misconfiguration | `GET /docs`, `GET /openapi.json` | [guide](../../../src/docs/vulns/api/API8-Security-Misconfiguration.md) |
| API9 | Improper Inventory Management | `GET /api/customers/_debug/{customerId}` | [guide](../../../src/docs/vulns/api/API9-Improper-Inventory-Management.md) |
| API10 | Unsafe Consumption of APIs | `POST /api/shop/webhooks/provisioning-callback` | [guide](../../../src/docs/vulns/api/API10-Unsafe-Consumption-of-APIs.md) |

## Two different origins, same "live" bar

- **API2, API4, API6, API8** were *pre-existing* — real gaps already shipping
  in the Phase 1/2 backend before this stage touched anything (same
  convention as M1/M3: "no code is added for these labs").
- **API1, API3, API5, API7, API9, API10** were *deliberately introduced* by
  stage 17 as small, targeted diffs to `src/backend` — each one adds new
  surface (a new endpoint, or a new field on an existing schema) rather than
  weakening an existing, correctly-written check. See each guide's "Where it
  lives" / "Why it is APIn" section for the exact diff and why the
  surrounding code was otherwise safe.

Both groups' weaknesses were confirmed by direct code read against a live
backend instance, but only the six newly-introduced ones had their exploit
actually re-run with the real response/state-change captured in the guide
("Verified exploitation"). The four pre-existing ones carry example `curl`
commands ("Dynamic exploitation") that were not re-executed and captured in
this stage — a follow-up noted below.

## How the newly-introduced six were verified (evidence, not assumption)

Verification run: a throwaway container (`python:3.12-slim`, SQLite dev DB,
`VULNMNO_ENV=dev`, seed data auto-applied), backend reachable on
`localhost:18000`, torn down afterward.

- **API1** — created a ticket as customer `CUST-10001`; confirmed the normal
  `GET /tickets/{id}` correctly 404s for customer `CUST-10003`; confirmed
  `GET /tickets/by-reference/{id}` returns `200` with `CUST-10001`'s ticket
  content to `CUST-10003`.
- **API3** — confirmed `loyaltyTier` was `bronze` for `CUST-10003`; PUT
  `{"loyaltyTier":"platinum"}` to `/contact-details`; confirmed it persisted
  (re-read `GET /me` afterward).
- **API5** — created a real purchase + refund request (`REF-10001`,
  `pending`); logged into the admin portal as `support` (`support_agent`,
  no `REFUND_WORKFLOW` grant); confirmed the real `/approve` route returns
  `403 ADMIN_FORBIDDEN`; confirmed `/quick-approve` returns `303` (success)
  and the refund shows `approved` when read back by a properly-privileged
  `billing` session.
- **API7** — registered a device with
  `callbackUrl=http://127.0.0.1:8000/api/customers/_debug/CUST-10001`;
  confirmed the backend's own uvicorn access log recorded a `127.0.0.1`
  (loopback, i.e. server-originated) hit to that exact path — proof the
  server, not the client, made the request.
- **API9** — called `GET /api/customers/_debug/CUST-10001` with **no**
  `Authorization` header; got `200` with the real Argon2 `password_hash`;
  confirmed the path is listed in `/openapi.json`.
- **API10** — created a purchase (balance `25.50 → 20.51`); POSTed
  `{"purchaseId":...,"status":"failed"}` to the webhook with **no**
  `Authorization` header and no signature; confirmed the balance was
  credited back to `25.50`.

Full transcripts (exact commands + real output) are in each guide, not
reproduced twice here.

## Next step

All ten are live and documented. Remaining optional follow-ups: wire CI
checks (the API9 openapi-diff, a webhook-signature test), decide whether any
of the six newly-introduced labs should ship disabled-by-default behind a
feature flag for non-training deployments, and re-run + capture real
transcripts for the four pre-existing categories (API2, API4, API6, API8) so
every guide carries the same evidentiary bar, not just the six introduced
here.

## Addendum (post-review fix)

A later review of this stage found `app/seed.py`'s `PROMO-SUMMER-2026`
(backing coupon `SUMMER20`, the API6 demo) anchored to a hardcoded
`2026-05-01` + 120-day window — which silently expired on 2026-08-29,
breaking the §9.2 promo-purchase journey, `tests/test_shop.py`, and the API6
lab itself once the host clock passed that date. Fixed by anchoring the seed
window to `datetime.now(UTC)` instead of a fixed calendar date. Full test
suite: 49/49 passing after the fix (was 48/49).
