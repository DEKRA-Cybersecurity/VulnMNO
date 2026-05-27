# Admin journey requirement template

Admin requirements differ from Phase 1 customer requirements in two ways:

1. **Actor is a role, not "Customer".** Use one of: `Support Agent`, `Billing Operator`, `Product Manager`, `Ops Admin`, `Security/Fraud Analyst`, `Supplier Admin` — matching `shared/glossary.md` §8.
2. **Related column points to `AEP-…` (admin HTML endpoint)** instead of `EP-…`, plus the `ADM-…` screen and `ENT-…` entities.

## Shape

```
| REQ-205 | admin | Billing Operator | As a Billing Operator I can adjust a customer's wallet balance with a justification. | Given a target customer and a non-zero `amount` with a `reason` ≥ 10 chars, when I POST /admin/customers/{id}/balance-adjust, then the balance is updated, a `Transaction(type=adjustment)` is created, an `AuditEvent ADMIN_BALANCE_ADJUSTMENT` is written with `actor_id=<admin.public_id>`, and the admin's role grants RW on the `customer_balance` module. | AEP-014, ADM-005, ENT-Balance, ENT-Transaction, ENT-AuditEvent |
```

## Rules

- Every mutation by an admin **must** include an `AuditEvent ADMIN_*` write in the acceptance criteria — no exceptions.
- Every admin action that surfaces in the UI must reference the RBAC module in `admin-rbac-matrix.md` (the matrix row).
- Use `OUT-OF-PHASE-2` to mark anything explicitly deferred (e.g., loyalty points redemption, multi-factor admin login).

## RBAC module names (lock these — they appear in both the matrix and `@require_role` decorators)

- `customer_search`
- `customer_balance`
- `plan_catalog`
- `promotion_catalog`
- `coupon_catalog`
- `ticket_management`
- `refund_workflow`
- `audit_log`
- `reporting`
- `admin_users_management`
