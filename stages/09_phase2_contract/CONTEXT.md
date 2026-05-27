# Stage 09 — Phase 2 contract

Extend the API surface to cover everything Stage 08 specified: admin portal HTML endpoints (AEP-…), loyalty JSON endpoints (EP-090, EP-091), gateway adapter Protocols, and new error codes. Stage 11 (admin build) and Stage 12 (integrations) consume this contract.

## Inputs

**Layer 4 (working):**
- `../08_phase2_requirements/output/backlog.md`
- `../08_phase2_requirements/output/traceability.md`
- `../08_phase2_requirements/output/admin-rbac-matrix.md`
- `../02_api_contract/output/openapi.yaml` (Phase-1 contract — extended here)
- `../02_api_contract/output/error-codes.md` (extended here)
- `../02_api_contract/output/auth-model.md`

**Layer 3 (reference):**
- `../02_api_contract/references/contract-rules.md` — same conventions (cursor pagination, money format, datetime, etc.).
- `../../_config/conventions.md` (updated in Stage 08 with new prefixes).

## Process

1. Author AEP entries for the 28 admin endpoints. Each has `Content-Type: text/html` (or `text/html; charset=utf-8` for fragments). Document the cookie auth requirement (`Cookie: vulnmno_admin_session=…`) and the CSRF token field for POST/PUT.
2. Author new JSON endpoints for loyalty (EP-090, EP-091).
3. Define the gateway adapter Protocols in `adapter-interfaces.md`. These are Python `Protocol` types (PEP 544), not OpenAPI schemas — they document the abstraction that Stage 12 implements.
4. Extend the master error-code list with `ADMIN_FORBIDDEN`, `ADMIN_SESSION_EXPIRED`, `PAYMENT_DECLINED`, `PROVISIONING_FAILED`, `PUSH_FAILED`, `LOYALTY_INSUFFICIENT_POINTS`.
5. Extend the consolidated `openapi.yaml` (copy of Phase-1 spec + admin/loyalty additions). Admin endpoints are tagged `admin`; loyalty `loyalty`.

## Outputs

Write to `output/`:

- `admin-endpoints.md` — AEP-001 … AEP-062 table (method, path, auth, request shape, response shape, errors, RBAC module → role).
- `loyalty-endpoints.md` — EP-090, EP-091.
- `adapter-interfaces.md` — Python `Protocol` definitions for PaymentGateway, ProvisioningClient, PushDelivery + the result types (`ChargeResult`, `ProvisionResult`, `SendResult`).
- `error-codes-delta.md` — the six new codes with HTTP status, used-by, description.
- `openapi.yaml` — consolidated spec (Phase 1 + Phase 2). Must pass `openapi-spec-validator`.

All `.md` outputs open with the four-section header (Scope / Inputs / Findings / Open questions).
