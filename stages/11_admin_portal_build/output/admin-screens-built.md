# Admin screens built — Stage 11

Mapping of every `ADM-…` from `09_phase2_contract/output/admin-endpoints.md` to the Jinja2 template + router that implements it.

| ADM | Name | Template | Router endpoint | Status |
| --- | --- | --- | --- | --- |
| ADM-001 | LoginPage | `templates/admin/login.html` | `routers/auth.py::login_form` + `login_submit` | ✅ |
| ADM-002 | LogoutLink (header) | (no template — POST form in `base.html`) | `routers/auth.py::logout` | ✅ |
| ADM-003 | CustomerSearch | `templates/admin/customers/search.html` + `_partials/customers_table.html` | `routers/customers.py::search` | ✅ |
| ADM-004 | CustomerDetail | `templates/admin/customers/detail.html` | `routers/customers.py::detail` | ✅ |
| ADM-005 | BalanceAdjust | `templates/admin/_partials/balance_card.html` | `routers/customers.py::balance_adjust` | ✅ |
| ADM-006 | PlanList | `templates/admin/plans/list.html` | `routers/plans.py::plans_list` + `plans_new` + `plans_archive` | ✅ |
| ADM-007 | PlanEdit | (inline in `plans/list.html` collapse) | `routers/plans.py::plans_new` | ✅ |
| ADM-008 | PromotionList | `templates/admin/promotions/list.html` | `routers/promotions.py::promo_list` + `promo_new` | ✅ |
| ADM-009 | CouponGenerator | (inline in `promotions/list.html` row form) | `routers/promotions.py::coupons_generate` | ✅ |
| ADM-010 | TicketList | `templates/admin/tickets/list.html` | `routers/tickets.py::tickets_list` | ✅ |
| ADM-011 | TicketDetail | `templates/admin/tickets/detail.html` | `routers/tickets.py::ticket_detail` + `agent_reply` + `ticket_close` | ✅ |
| ADM-012 | RefundList | `templates/admin/refunds/list.html` | `routers/refunds.py::refunds_list` + `refund_approve` + `refund_reject` | ✅ |
| ADM-013 | AuditLogViewer | `templates/admin/audit/list.html` | `routers/audit.py::audit_list` | ✅ |
| ADM-014 | ReportingDashboard | `templates/admin/reports.html` | `routers/reports.py::reports` | ✅ |
| ADM-015 | AdminUsersAdmin | `templates/admin/staff/list.html` | `routers/admin_users.py::staff_list` + `staff_new` + `staff_deactivate` | ✅ |

**15/15 ADM screens scaffolded and runtime-verified.**

## Cross-cutting infrastructure under `app/admin/`

| Concern | Where |
| --- | --- |
| Session cookie + CSRF | `app/admin/security.py` |
| RBAC matrix (single source) | `app/admin/permissions.py` |
| Auth + RBAC + CSRF dependencies | `app/admin/deps.py` |
| Jinja2 environment + filters (`money`, `dt`, `csrf_input`) | `app/admin/templates_loader.py` |
| Admin-scoped audit writer | `app/admin/services/audit.py` |
| Aggregated router | `app/admin/routers/__init__.py` |
| Static assets | `static/admin/admin.css` + `admin.js` (HTMX from CDN) |
| App wiring | `app/main.py` (StaticFiles mount + SessionMiddleware + AppError HTML handler + include `admin_router`) |

## HTMX patterns in use

- **CustomerSearch:** `<form hx-get="/admin/customers" hx-target="#results" hx-push-url="true">` — server returns `_partials/customers_table.html` when `HX-Request: true`.
- **BalanceAdjust:** `<form hx-post hx-target="#balance-card" hx-swap="outerHTML" hx-confirm>` — swaps the balance card with the refreshed partial.
- **Plans / Promotions:** standard form POST → 303 redirect → re-fetch list (no HTMX). HTMX patterns documented for future incremental upgrade.

## Tests

- `tests/admin/test_auth_and_rbac.py` — 7 tests: anonymous redirect, login form, wrong password, good login, RBAC denial (support_agent → balance adjust), RBAC allow (billing_operator → balance adjust), audit read (security_analyst), staff denied (security_analyst).
- `tests/admin/test_screens.py` — 12 tests: dashboard, customer search, customer detail, customer 404, plans list, promotions list, tickets list, refunds list, audit list, reports, staff list (ops_admin).
- **Result:** `pytest tests/admin -q` → **19/19 passed in 2.80s**.

## Notes / deviations from the contract

- `templates/admin/plans/edit.html` and `templates/admin/promotions/edit.html` standalone pages were folded into the list pages' Bootstrap collapse form to keep file count manageable. The contract's AEP-022 / AEP-026 (edit endpoints) are not used in the current UI — listed as `OUT-OF-PHASE-2` extensions.
- The `app.exception_handler(AppError)` in `app/main.py` was extended to detect `/admin/*` requests and render a Bootstrap error page instead of a JSON envelope. Mobile API behavior is unchanged.
- **Refund approve** marks `Refund.status='approved'` and appends a `TicketMessage`. The wallet-credit side effect (creating a refund `Transaction`) is deferred to Stage 12's `app/services/refund.py` — Stage 11 implements the UI + audit + status flip only.
- **Plan/Promotion archiving** uses the `eligibility_rules` JSON column (`{"archived": true}`) since the existing Phase-1 schema has no `status` column on those tables. Phase 3 could add one.
