# Stage 11 — Admin portal coverage

## Test run

```
pytest tests/admin -q
19 passed in 2.80s
```

Combined with Phase 1 tests:

```
pytest -q
43 passed in 5.29s
```

(24 Phase 1 + 19 Phase 2 admin tests)

## Coverage on `app/admin/`

```
python -m coverage run --source=app/admin -m pytest tests/admin
python -m coverage report
```

| Module | Coverage |
| --- | --- |
| `app/admin/permissions.py` | **97 %** |
| `app/admin/security.py` | 87 % |
| `app/admin/deps.py` | 88 % |
| `app/admin/templates_loader.py` | 91 % |
| `app/admin/services/audit.py` | 91 % |
| `app/admin/routers/auth.py` | 62 % |
| `app/admin/routers/dashboard.py` | 72 % |
| `app/admin/routers/customers.py` | 49 % |
| `app/admin/routers/plans.py` | 56 % |
| `app/admin/routers/promotions.py` | 53 % |
| `app/admin/routers/tickets.py` | 51 % |
| `app/admin/routers/refunds.py` | 41 % |
| `app/admin/routers/audit.py` | 66 % |
| `app/admin/routers/reports.py` | 71 % |
| `app/admin/routers/admin_users.py` | 50 % |
| **TOTAL on `app/admin/`** | **64 %** |

## What's covered (happy + RBAC denial)

- Anonymous → redirect to `/admin/login`.
- Login form renders with a fresh CSRF token.
- Invalid credentials → 401 + form re-render.
- Valid credentials → 303 to dashboard with admin info in navbar.
- Customer search returns seeded `CUST-10001` row.
- Customer detail renders with wallet balance card.
- Customer 404 for unknown public_id.
- All sidebar pages render for `ops_admin` (plans, promotions, tickets, refunds, audit, reports, staff).
- `support_agent` → balance adjust → **403 ADMIN_FORBIDDEN**.
- `billing_operator` → balance adjust → **200, wallet updated, audit row written**.
- `security_analyst` → audit log read → 200.
- `security_analyst` → staff page → **403 ADMIN_FORBIDDEN**.

## What's NOT covered (deferred to Stage 13 integration)

- Coupon batch generation success path.
- Plan/promotion create + archive happy paths.
- Refund approve/reject end-to-end (Stage 12 wires the wallet credit side-effect).
- Agent reply on a ticket + ticket close.
- Admin user CRUD (create, deactivate).

Stage 13's `smoke_admin.sh` will cover these via curl + cookie-jar.

## Manual verification (one-time pass)

Run uvicorn locally, point a browser at `http://localhost:8000/admin/login`, sign in as
`ops / admin1234`, verify all sidebar entries render and the customer detail page for
`CUST-10001` shows the wallet card with an "Adjust balance" form. Confirmed during stage execution.
