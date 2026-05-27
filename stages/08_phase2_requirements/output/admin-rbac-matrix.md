# Admin RBAC matrix — Phase 2

## Scope

Single source of truth for **which admin role can do what**. Stage 11's `app/admin/permissions.py` is generated directly from this matrix: each `(role, module)` cell with `RW` permits both reads and writes; `R` permits reads only; `-` denies. Stage 11 `@require_role` decorators consult this matrix at request time.

## Inputs consumed

- `docs/VulnMNO.md` §8 (role definitions).
- `references/admin-journeys-template.md` (module name list — locked).
- `stages/01_requirements/output/backlog.md` (OUT-OF-PHASE-1 hints about who does what).

## Findings

### Roles (per `docs/VulnMNO.md` §8)

- **support_agent** — front-line customer assistance.
- **billing_operator** — payments, refunds, balance adjustments.
- **product_manager** — catalog (plans, promotions, coupons).
- **ops_admin** — platform operations, admin user management.
- **security_analyst** — read access to audit logs and reports for fraud review.
- **supplier_admin** — limited scope; sees only their assigned supplier components (out of scope for Phase 2's MVP — placeholder row, denied everywhere except its own future scope).

### Modules and permissions

| Module | support_agent | billing_operator | product_manager | ops_admin | security_analyst | supplier_admin |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| `customer_search` | R | R | R | R | R | - |
| `customer_balance` | - | RW | - | RW | - | - |
| `plan_catalog` | R | R | RW | RW | R | - |
| `promotion_catalog` | R | R | RW | RW | R | - |
| `coupon_catalog` | R | R | RW | RW | R | - |
| `ticket_management` | RW | R | R | RW | R | - |
| `refund_workflow` | - | RW | - | RW | - | - |
| `audit_log` | - | R | - | R | R | - |
| `reporting` | - | R | R | R | R | - |
| `admin_users_management` | - | - | - | RW | - | - |

### Notes

- **support_agent** is intentionally *not* given balance adjustment (cf. `docs/VulnMNO.md` §13.3 fraud-relevant statement "Support agents may manually adjust balances" — Phase 2 reduces this risk by funneling balance changes through billing_operator + ops_admin only). Stage 11 documents this deviation in its `output/admin-screens-built.md`.
- **security_analyst** has read access to `audit_log`, `reporting`, and catalog reads for context, but no write anywhere.
- **ops_admin** is the only role that can manage other admin users.
- **supplier_admin** is a placeholder for Phase 3 supplier-portal work; in Phase 2 it has zero permissions and cannot log in.

## Open questions

- **Multi-factor admin login.** Out of Phase 2 scope. `ops_admin` accounts SHOULD have it in Phase 3. Document in backlog `OUT-OF-PHASE-2`.
- **Per-supplier isolation** for `supplier_admin`. Deferred to Phase 3.
