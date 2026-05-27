# End-to-end rules

## When does a journey "pass"?

A journey passes when **all** of the following hold against the seeded backend:

1. Every step listed in the `INT-…` case's `Steps` column executes without an unexpected error.
2. Every UI assertion (text visible, navigation reached, badge updated) holds.
3. Every backend assertion (DB row created / updated, audit event written, balance adjusted) holds.
4. No unhandled exception in the FastAPI logs during the run.
5. The acceptance criteria in `01_requirements/output/backlog.md` for the journey's `REQ-…` rows are visibly satisfied.

A journey can pass with **known deltas** (documented in `output/contract-deltas.md` referenced from this stage). It cannot pass with undocumented divergence.

## Recording a run

Each integration run produces one entry in `run-log.md`:

```
## 2026-05-26 14:22 UTC — backend@<sha>, android@<sha>
| INT-001 §9.1 login           | PASS |       |
| INT-002 §9.2 purchase w/promo| PASS |       |
| INT-003 §9.3 plan change     | FAIL | promo `STACK5` shows `Promotion ineligible` on `CUST-10003` (postpaid) — open ticket #… |
| INT-004 §9.4 usage           | PASS |       |
| INT-005 §9.5 invoice review  | PASS |       |
| INT-006 §9.6 support ticket  | PASS |       |
```

`<sha>` is the short git SHA of each project's `output/` at run time. Get both with `git rev-parse --short HEAD` from each project root.

## Smoke script conventions

`smoke_api.sh`:

- Bash, `set -euo pipefail`.
- One section per endpoint group.
- Reads base URL from `${BASE_URL:-http://localhost:8000}`.
- Authenticates once at the top using a seeded customer; reuses the token for the rest.
- Asserts response status codes only — not exact payloads (the backend test suite is the place for that). Exits non-zero on the first failure.

`smoke_mobile.md`:

- Markdown checklist, one section per journey.
- Each step names the expected UI element (e.g. "Balance card shows `25,50 €`") so a tester can verify without consulting the spec.
- Reset state instruction at the top: re-run `app/seed.py` on the backend before the mobile pass to guarantee deterministic seeds.

## Reproducibility

- The seeded DB state is the contract for E2E. If a journey only passes on a hand-tweaked DB, that's a bug in `app/seed.py` (stage 04), not a passing journey.
- Time-dependent assertions (e.g. "invoice for period 2026-05") must use the seed's fixed dates, not the wall clock. The seed places fixtures at known dates in May 2026 to match `docs/VulnMNO.md` §13 example timestamps.

## What stage 07 does NOT do

- It does not add new endpoints, new screens, or new tests beyond integration glue. If a journey reveals a missing capability, the fix goes back to the owning stage (01–06), not here.
- It does not modify code under `04_api_build/output/backend/` or `06_mobile_build/output/android/`. The integration layer is glue, scripts, compose file, and the workspace README — nothing else.
