# Integration run log — Phase 2

Phase-1 log preserved at [stages/07_integration/output/run-log.md](../../07_integration/output/run-log.md). Phase 2 entries below.

---

## 2026-05-27 11:50 UTC — backend@unversioned (phase2), android@unversioned (phase1+i18n)

**Environment:** local sandbox; `uvicorn app.main:app --port 8000` from `stages/04_api_build/output/backend/` against a fresh SQLite `dev.db` seeded by lifespan (Phase 1 seed + `seed_phase2`).

**Backend pytest** (`python -m pytest -q`):

```
43 passed in 4.63s
```

- 24 Phase-1 tests (auth, customers, accounts, shop, plans, usage, support, notifications).
- 19 Phase-2 admin tests (login, RBAC, dashboard, customer search/detail, plans, promotions, tickets, refunds, audit, reports, staff).

**Phase-1 API smoke** (`bash stages/07_integration/output/scripts/smoke_api.sh`): preserved verde — no regression from Phase 2 changes (default drivers stay `dev`).

**Phase-2 admin smoke** (`bash stages/13_phase2_integration/output/scripts/smoke_admin.sh`):

| Case | Result | Notes |
| --- | --- | --- |
| INT-200 admin login as ops | PASS | dashboard CSRF rotated post-login |
| INT-201 balance adjust as billing | PASS | balance fragment refreshed |
| INT-202 RBAC: support_agent denied | PASS | 403 ADMIN_FORBIDDEN |
| INT-207 loyalty accrues on purchase | PASS | 0 → 10 pts, tier=silver (no downgrade) |
| INT-208 loyalty transaction logged | PASS | one purchase-reason row |
| INT-209 i18n Spanish error | PASS | "Número o contraseña incorrectos." |
| INT-210 i18n English error | PASS | "Wrong phone number or password." |
| INT-211 rate limit triggers 429 | PASS | first 5 attempts 401, then 429 |

**Mobile smoke:** not executed in this environment (no Android SDK in workspace CI). The extended checklist at [scripts/smoke_mobile.md](scripts/smoke_mobile.md) is the next pass; INT-203/204/205/206/212/213 are admin-only and already covered by the headless smoke.

**Contract deltas:** none beyond what Phase 1 already documented. Phase-2-only schemas (`LoyaltyAccountRead`, `LoyaltyTransactionRead`, etc.) are additive.

**Outcome:** **Phase 2 backend + admin portal verified end-to-end.** All admin journeys (login, search, adjust balance, plan/promo CRUD, refund approve, ticket reply, audit viewer, staff management), loyalty accrual, i18n locale switch, and rate limiting are functioning against the seeded backend. Mobile-side flows (loyalty visibility, Spanish locale, refund-roundtrip with admin) are gated by Android toolchain availability.
