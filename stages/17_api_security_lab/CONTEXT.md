# Stage 17 — API security lab (OWASP API Security Top 10)

## Purpose

Seed the **OWASP API Security Top 10 (2023)** as a documented, *verified*
training-lab surface across the FastAPI backend — the API-side counterpart
to the existing OWASP Mobile Top 10 surface (M1 / M3) already shipping in
`src/docs/vulns/mobile/`. Same spirit as stages 15/16 (which built the M1 L3
/ M3 L3 TLS-downgrade lab): deliberate, catalogued weaknesses with
static-analysis hints, exploitation steps, blue-team detection queries, and
a remediation diff — not a threat-model or controls review (that stays
Phase 3 / out of scope per the root `README.md`).

This stage ran in two passes:

1. **Documentation pass.** Each of the ten OWASP API categories was checked
   against the real Phase 1/2 backend and classified **Live** (the weakness
   already shipped — API2, API4, API6, API8) or **Planned** (the target zone
   was already correctly defended, so the guide specced the exact diff that
   would introduce the lab, bannered "not yet implemented"). No backend code
   was touched in this pass.
2. **Implementation + verification pass.** The six Planned diffs (API1, API3,
   API5, API7, API9, API10) were applied to `src/backend`, then every one of
   the ten labs — the four pre-existing plus the six newly introduced — was
   exercised against a live instance (throwaway container, SQLite dev DB,
   seed data) with real `curl`/admin-portal requests. Each guide's "Verified
   exploitation" section carries the actual commands and actual captured
   output, not a hypothetical. **All ten are now live.**

## Inputs

**Layer 4 (working):**

- `../../src/backend/app/routers/*.py`, `../../src/backend/app/admin/routers/*.py`
  — every endpoint was enumerated and read to classify Live vs Planned, then
  the six Planned ones were edited directly (`support.py`, `customers.py`,
  `admin/routers/refunds.py`, `auth.py`, `shop.py`).
- `../../src/backend/app/schemas/{customer,auth}.py` — extended
  (`ContactDetailsUpdate.loyaltyTier`, `DeviceRegisterRequest.callbackUrl`).
- `../../src/backend/app/services/auth.py`, `services/shop.py` — business
  logic behind the auth and promo flows (read, not modified — API2/API6 stay
  pre-existing).
- `../../src/backend/app/config.py`, `rate_limit.py`, `main.py`,
  `permissions.py`, `admin/deps.py` — settings, rate-limit wiring,
  CORS/middleware config, RBAC (`get_current_admin` vs `require_module`).
- `../../src/backend/app/gateways/{payment,provisioning}.py` — outbound
  third-party calls (read, not modified — API10 was reimplemented as an
  inbound webhook instead, see mapping doc's rationale).
- `../../src/docs/vulns/mobile/M3-Insecure-Authentication-Authorization.md` —
  the OTP/password-reset brute-force lab already documents the same root
  cause this stage maps to API2; the API2 doc cross-references it instead of
  duplicating it.
- `../../README.md` — "Training-lab surface" section, extended with an API
  sub-section.

**Layer 3 (reference):**

- `docs/VulnMNO.md` §9 (customer journeys), §12/§13 (API surface + examples).
- `stages/02_api_contract/output/openapi.yaml` — canonical contract, used as
  the "what should exist" baseline for the API9 (inventory) entry.

## Process

1. Enumerate every `@router.*` decorator in `app/routers/` and
   `app/admin/routers/`.
2. For each of the 10 OWASP API Top 10:2023 categories, find the closest real
   endpoint ("zona") and read the backing service/model code to determine
   whether the flaw was already present or already mitigated.
3. Write a full pentest guide in `src/docs/vulns/api/APIn-Name.md` per
   category, matching the M1/M3 template: OWASP reference, *Where it lives*,
   *Why it is APIn*, *How to find it (static analysis)*, exploitation,
   *Blue-team detection*, *Remediation diff*.
4. For the six categories that weren't already live, apply the smallest
   deliberate diff that introduces the lab as **new** surface (a new
   endpoint or a new field on an existing schema) rather than weakening an
   existing, correctly-written check.
5. Stand up a throwaway backend instance (Python container, SQLite,
   `VULNMNO_ENV=dev`, seed data) and run every guide's exploitation steps for
   real; capture the actual commands and actual output into each guide.
   Tear the instance down afterward; discard the generated `dev.db`.
6. Update the root `README.md` "Training-lab surface" section listing all
   ten guides.
7. Record evidence (file:line citations, verification transcript summary) in
   `output/run-log.md`.

## Outputs

- `references/owasp-api-top10-mapping.md` — full 10-row mapping, zone per
  category, verification summary, and a link to each guide.
- `output/run-log.md` — evidence trail for both passes.
- `../../src/backend/app/routers/support.py` — `get_ticket_by_reference` (API1)
- `../../src/backend/app/schemas/customer.py` — `ContactDetailsUpdate.loyaltyTier` (API3)
- `../../src/backend/app/routers/customers.py` — loyaltyTier write path (API3) + `debug_dump_customer` (API9)
- `../../src/backend/app/admin/routers/refunds.py` — `refund_quick_approve` (API5)
- `../../src/backend/app/schemas/auth.py` — `DeviceRegisterRequest.callbackUrl` (API7)
- `../../src/backend/app/routers/auth.py` — SSRF fetch in `register_device` (API7)
- `../../src/backend/app/routers/shop.py` — `provisioning_callback` webhook (API10)
- `../../src/docs/vulns/api/API1-Broken-Object-Level-Authorization.md` (live)
- `../../src/docs/vulns/api/API2-Broken-Authentication.md` (live)
- `../../src/docs/vulns/api/API3-Broken-Object-Property-Level-Authorization.md` (live)
- `../../src/docs/vulns/api/API4-Unrestricted-Resource-Consumption.md` (live)
- `../../src/docs/vulns/api/API5-Broken-Function-Level-Authorization.md` (live)
- `../../src/docs/vulns/api/API6-Unrestricted-Access-to-Sensitive-Business-Flows.md` (live)
- `../../src/docs/vulns/api/API7-Server-Side-Request-Forgery.md` (live)
- `../../src/docs/vulns/api/API8-Security-Misconfiguration.md` (live)
- `../../src/docs/vulns/api/API9-Improper-Inventory-Management.md` (live)
- `../../src/docs/vulns/api/API10-Unsafe-Consumption-of-APIs.md` (live)
- `../../README.md` — Training-lab surface section extended.

## Out of scope

- Threat model, fraud scenarios, controls review — still Phase 3, still a
  separate analytical workspace per the root `README.md`.
- Rewriting or removing the existing M1/M3 mobile docs. API2 cross-references
  M3 L1/L2 rather than restating them.
- CI enforcement (an openapi-diff gate for API9, a webhook-signature test for
  API10) — noted as a follow-up in the mapping doc, not built here.
- Shipping any of the six newly-introduced labs disabled-by-default behind a
  feature flag for non-training deployments — also a follow-up, not decided
  yet.
