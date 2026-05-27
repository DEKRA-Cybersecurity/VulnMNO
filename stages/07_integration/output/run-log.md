# Integration run log

One block per run. Append at the bottom. Get SHAs with `git rev-parse --short HEAD` from each project root.

---

## 2026-05-27 09:23 UTC — backend@unversioned, android@unversioned

**Environment:** local sandbox; `uvicorn app.main:app --port 8000` from `stages/04_api_build/output/backend/` against a fresh SQLite `dev.db` seeded via lifespan.

**API smoke** (`bash stages/07_integration/output/scripts/smoke_api.sh`):

| Case | Result | Notes |
| --- | --- | --- |
| INT-001 §9.1 Login (Alice) | PASS | tokens issued; profile/balance/plan/featured all 200 |
| INT-002 §9.1 OTP (Bruno, code 123456) | PASS | challenge issued, verify → tokens |
| INT-003 §9.2 Purchase + promo SUMMER20 | PASS | finalPrice 7.99; purchase confirmed/active; balance 25.50 → 17.51 |
| INT-004 §9.3 Plan change PREPAID-BASIC immediate | PASS | status applied |
| INT-004b §9.3 Plan ineligible UNLIMITED-PREMIUM | PASS | 400 PLAN_INELIGIBLE |
| INT-005 §9.4 Usage tabs + invalid range | PASS | calls/sms/data/roaming 200; from>to → 400 VALIDATION_FAILED |
| INT-006 §9.5 Invoice INV-20001 + PDF (Bruno) | PASS | 1 line item; `application/pdf` |
| INT-007 §9.6 Ticket lifecycle | PASS | created → message → close → TICKET_CLOSED on next message |
| INT-008 Refresh + chain reuse | PASS | first refresh OK; reuse → TOKEN_REVOKED |
| INT-009 Cross-customer 404 | PASS | Alice → INV-20001 (Bruno's) → 404 |
| INT-010 Wrong password | PASS | 401 INVALID_CREDENTIALS |

**Mobile smoke:** not executed in this environment (no Android SDK / emulator in the workspace's CI image). Stage 06 deliverable is reviewed statically; the walkthrough in [scripts/smoke_mobile.md](scripts/smoke_mobile.md) is the next pass.

**Contract deltas:** none beyond those already documented in [04_api_build/output/contract-deltas.md](../../04_api_build/output/contract-deltas.md) (schema-naming only).

**Outcome:** Phase-1 API surface verified end-to-end against the seeded backend. The mobile pass is gated by access to an Android toolchain.
