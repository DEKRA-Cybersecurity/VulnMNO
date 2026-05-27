# Admin portal endpoints (AEP)

## Scope

28 HTML endpoints under `/admin/*`. All except the login pair require an authenticated admin session (cookie `vulnmno_admin_session`). All POST/PUT/DELETE require a CSRF token field `csrf_token` in the form body. Responses are `text/html` (full page) or `text/html; charset=utf-8` (HTMX fragment when the request carries `HX-Request: true`).

## Inputs consumed

- `../08_phase2_requirements/output/backlog.md`
- `../08_phase2_requirements/output/traceability.md`
- `../08_phase2_requirements/output/admin-rbac-matrix.md`
- `../02_api_contract/output/auth-model.md` (cookie session model designed here, JWT model untouched).

## Findings

### auth (no session required)

| ID | Method | Path | Body | Returns | Errors | RBAC |
| --- | --- | --- | --- | --- | --- | --- |
| AEP-001 | GET | `/admin/login` | — | Login form (HTML) with CSRF token in hidden input | — | any (or anonymous) |
| AEP-002 | POST | `/admin/login` | `username`, `password`, `csrf_token` | 302 → `/admin/` (or `?next=…`) on success; 200 with form + error banner on failure | — | any |
| AEP-003 | POST | `/admin/logout` | `csrf_token` | 302 → `/admin/login` | — | any (authenticated) |

### dashboard

| ID | Method | Path | Returns | RBAC |
| --- | --- | --- | --- | --- |
| AEP-004 | GET | `/admin/` | Dashboard HTML — KPI tiles + recent admin actions feed | any role |

### customers

| ID | Method | Path | Returns | Errors | RBAC |
| --- | --- | --- | --- | --- | --- |
| AEP-010 | GET | `/admin/customers?q=<term>&limit=&cursor=` | Search results table (HTML or fragment if `HX-Request`) | — | `customer_search:R` |
| AEP-011 | GET | `/admin/customers/{customerId}` | Customer detail page with tabs | `NOT_FOUND` | `customer_search:R` |
| AEP-012 | GET | `/admin/customers/{customerId}/transactions?limit=&cursor=` | Transactions fragment | `NOT_FOUND` | `customer_search:R` |
| AEP-013 | GET | `/admin/customers/{customerId}/purchases?limit=&cursor=` | Purchases fragment | `NOT_FOUND` | `customer_search:R` |
| AEP-014 | POST | `/admin/customers/{customerId}/balance-adjust` | Body: `amount`, `reason`, `csrf_token`. Returns updated balance card fragment + flash message. | `VALIDATION_FAILED`, `NOT_FOUND`, `ADMIN_FORBIDDEN` | `customer_balance:RW` |

### plans

| ID | Method | Path | Returns | Errors | RBAC |
| --- | --- | --- | --- | --- | --- |
| AEP-020 | GET | `/admin/plans` | List page (HTML or fragment) | — | `plan_catalog:R` |
| AEP-021 | POST | `/admin/plans/new` | Body: plan fields + `csrf_token`. Returns redirect to detail or list. | `VALIDATION_FAILED`, `CONFLICT` (dup public_id) | `plan_catalog:RW` |
| AEP-022 | POST | `/admin/plans/{planId}/edit` | Body: editable fields. Updates plan. | `NOT_FOUND`, `VALIDATION_FAILED` | `plan_catalog:RW` |
| AEP-023 | POST | `/admin/plans/{planId}/archive` | Marks plan archived (status). | `NOT_FOUND`, `CONFLICT` | `plan_catalog:RW` |

### promotions

| ID | Method | Path | Returns | Errors | RBAC |
| --- | --- | --- | --- | --- | --- |
| AEP-024 | GET | `/admin/promotions` | List | — | `promotion_catalog:R` |
| AEP-025 | POST | `/admin/promotions/new` | Body: promo fields + initial coupon `count`. | `VALIDATION_FAILED` | `promotion_catalog:RW` |
| AEP-026 | POST | `/admin/promotions/{promoId}/edit` | Update | `NOT_FOUND`, `VALIDATION_FAILED` | `promotion_catalog:RW` |
| AEP-027 | POST | `/admin/promotions/{promoId}/archive` | Archive | `NOT_FOUND` | `promotion_catalog:RW` |
| AEP-028 | POST | `/admin/promotions/{promoId}/coupons/generate` | Body: `count` (1–1000). Creates that many `Coupon` rows. | `VALIDATION_FAILED`, `NOT_FOUND` | `coupon_catalog:RW` |

### tickets

| ID | Method | Path | Returns | Errors | RBAC |
| --- | --- | --- | --- | --- | --- |
| AEP-030 | GET | `/admin/tickets?status=&topic=&limit=&cursor=` | List | — | `ticket_management:R` |
| AEP-031 | GET | `/admin/tickets/{ticketId}` | Detail | `NOT_FOUND` | `ticket_management:R` |
| AEP-032 | POST | `/admin/tickets/{ticketId}/agent-reply` | Body: `body`, `csrf_token`. Creates `TicketMessage(author_role=agent)`. | `NOT_FOUND`, `TICKET_CLOSED`, `VALIDATION_FAILED` | `ticket_management:RW` |
| AEP-033 | POST | `/admin/tickets/{ticketId}/close` | Closes the ticket. | `NOT_FOUND`, `CONFLICT` | `ticket_management:RW` |

### refunds

| ID | Method | Path | Returns | Errors | RBAC |
| --- | --- | --- | --- | --- | --- |
| AEP-040 | GET | `/admin/refunds?status=&limit=&cursor=` | List | — | `refund_workflow:R` |
| AEP-041 | POST | `/admin/refunds/{refundId}/approve` | Body: `note`, `auto_close`, `csrf_token`. Side effects per REQ-241. | `NOT_FOUND`, `CONFLICT` (already approved/rejected) | `refund_workflow:RW` |
| AEP-042 | POST | `/admin/refunds/{refundId}/reject` | Body: `reason`, `csrf_token`. | `NOT_FOUND`, `CONFLICT`, `VALIDATION_FAILED` | `refund_workflow:RW` |

### audit

| ID | Method | Path | Returns | RBAC |
| --- | --- | --- | --- | --- |
| AEP-050 | GET | `/admin/audit?event_type=&actor_id=&from=&to=&limit=&cursor=` | Audit table (HTML or fragment) | `audit_log:R` |

### reports

| ID | Method | Path | Returns | RBAC |
| --- | --- | --- | --- | --- |
| AEP-051 | GET | `/admin/reports` | KPI dashboard | `reporting:R` |

### admin users (staff)

| ID | Method | Path | Returns | Errors | RBAC |
| --- | --- | --- | --- | --- | --- |
| AEP-060 | GET | `/admin/staff` | Admin user list | — | `admin_users_management:R` (ops_admin only per matrix) |
| AEP-061 | POST | `/admin/staff/new` | Body: `username`, `password`, `role`, `full_name`, `csrf_token`. | `VALIDATION_FAILED`, `CONFLICT` (dup username) | `admin_users_management:RW` |
| AEP-062 | POST | `/admin/staff/{adminId}/deactivate` | Sets status=`deactivated`. | `NOT_FOUND`, `CONFLICT` | `admin_users_management:RW` |

## Conventions

- **Cookie:** `vulnmno_admin_session` — HttpOnly, Secure (in prod-like), SameSite=Lax, signed via Starlette's SessionMiddleware (key from `VULNMNO_ADMIN_SESSION_SECRET`).
- **CSRF token:** issued at first GET of a form-bearing page, persisted in the session, validated on every POST/PUT/DELETE. Mismatched/missing token → 403 with `ADMIN_FORBIDDEN`.
- **HTMX detection:** routers check `request.headers.get("HX-Request") == "true"`; when true, return the `_partials/*.html` fragment instead of the full page.
- **Error rendering:** AppError exceptions render through an admin-aware handler that picks the right Jinja error template (full page) or fragment (`_partials/_error.html`) based on HTMX.
- **Pagination:** same cursor convention as Phase-1 API. URL params `limit` (default 20, max 100) and `cursor` (opaque base64url).

## Open questions

None remaining.
