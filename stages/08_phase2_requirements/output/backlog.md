# Phase 2 backlog

## Scope

Functional backlog covering everything OUT-OF-PHASE-1: admin portal journeys, payment/provisioning/FCM integrations, agent ticket replies, refund dispute workflow, internationalization, rate limiting, loyalty engine, and campaign management automation. One row per acceptance criterion using Given / When / Then. IDs start at `REQ-200` per the convention.

## Inputs consumed

- `docs/VulnMNO.md` §7.13, §8, §13.
- `stages/01_requirements/output/backlog.md` (OUT-OF-PHASE-1 list).
- `_config/conventions.md` (updated with `ADM-`, `AEP-`, `GW-`, `LOY-`).
- `stages/08_phase2_requirements/references/admin-journeys-template.md`.

## Findings

### Admin portal — auth + session

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-200 | admin/auth | any staff | Sign in to the admin portal with username + password. | Given a valid admin username and password, when I POST `/admin/login` with form-encoded credentials, then a signed session cookie is set, the response is 302 to `/admin/`, and an `AuditEvent ADMIN_LOGIN_SUCCESS` is written with `actor_id=<admin.public_id>` and the request IP. | AEP-001, AEP-002, ADM-001, ENT-AdminUser, ENT-AuditEvent |
| REQ-201 | admin/auth | any staff | Receive a clean denial on wrong credentials. | Given any username and an incorrect password, when I POST `/admin/login`, then the response is 200 (re-renders the login form with an error banner; no auth side-effect), and an `AuditEvent ADMIN_LOGIN_FAILED` is written with the attempted username and IP. | AEP-001, ADM-001 |
| REQ-202 | admin/auth | any staff | End my admin session. | Given an active admin cookie session, when I POST `/admin/logout`, then the session is invalidated, the cookie is cleared, the response is 302 to `/admin/login`, and an `AuditEvent ADMIN_LOGOUT` is written. | AEP-003, ENT-AdminUser |
| REQ-203 | admin/auth | any staff | Be redirected to login when session expires. | Given an expired or missing session cookie, when I GET any `/admin/*` (except login), then the response is 302 to `/admin/login?next=<original-path>`. | AEP-* (all protected) |
| REQ-204 | admin/auth | any staff | CSRF-protected mutations. | Given any POST/PUT/DELETE under `/admin/*` without a matching CSRF token in the form body, then the response is 403 with `ADMIN_FORBIDDEN`. | all admin write endpoints |

### Admin portal — customer search & detail

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-210 | admin/customers | any staff with `customer_search:R` | Search for customers by msisdn, name or customer ID. | Given an authenticated session with `customer_search:R` and a non-empty query, when I GET `/admin/customers?q=<term>`, then the response is 200 with an HTML table of up to 50 matches; HTMX request returns only the table fragment. | AEP-010, ADM-003, ENT-Customer |
| REQ-211 | admin/customers | any staff with `customer_search:R` | View a customer's full detail page. | Given an existing customer, when I GET `/admin/customers/{customerId}`, then the page renders overview, lines, balance, recent transactions (10), recent purchases (10), current plan, and open tickets (5) in tabs. Forbidden role → 403 with `ADMIN_FORBIDDEN`. | AEP-011…AEP-013, ADM-004, ENT-Customer, ENT-Balance, ENT-Transaction, ENT-Purchase, ENT-Plan, ENT-SupportTicket |
| REQ-212 | admin/customers | billing_operator OR ops_admin | Adjust a customer's wallet balance. | Given a customer, an `amount` (positive or negative, ≤ €500 absolute), and a `reason` ≥ 10 chars, when I POST `/admin/customers/{id}/balance-adjust`, then the wallet is updated, a `Transaction(type=adjustment, amount=…)` is created, and an `AuditEvent ADMIN_BALANCE_ADJUSTMENT` is written. Other roles → 403. | AEP-014, ADM-005, ENT-Balance, ENT-Transaction, ENT-AuditEvent |

### Admin portal — plan / promotion / coupon CRUD

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-220 | admin/plans | product_manager OR ops_admin | List, create, edit, archive plans. | Given the role, when I GET `/admin/plans` I see the catalog; POST `/admin/plans/new` with valid fields creates a Plan and writes `ADMIN_PLAN_CREATED`; POST `/admin/plans/{planId}/edit` updates and writes `ADMIN_PLAN_UPDATED`; POST `/admin/plans/{planId}/archive` marks status archived and writes `ADMIN_PLAN_ARCHIVED`. | AEP-020…AEP-023, ADM-006, ADM-007, ENT-Plan, ENT-AuditEvent |
| REQ-221 | admin/promotions | product_manager OR ops_admin | CRUD promotions. | Similar to REQ-220 over `/admin/promotions/*`. Includes promotion + linked coupon batch creation in one form. | AEP-024…AEP-027, ADM-008, ENT-Promotion |
| REQ-222 | admin/coupons | product_manager OR ops_admin | Generate coupon batches for an existing promotion. | Given a promotion and a `count` (1–1000), when I POST `/admin/promotions/{promoId}/coupons/generate`, then `count` new `Coupon` rows are created with unique codes and `usage_limit=1`, and `ADMIN_COUPONS_GENERATED` is audited. | AEP-028, ADM-009, ENT-Coupon |

### Admin portal — support ticket workflow

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-230 | admin/tickets | support_agent OR ops_admin | Browse all open tickets across customers. | GET `/admin/tickets?status=open&topic=Billing` returns a paginated list (20/page) with customer, topic, last-activity column. | AEP-030, ADM-010, ENT-SupportTicket |
| REQ-231 | admin/tickets | support_agent OR ops_admin | View ticket detail with all messages. | GET `/admin/tickets/{ticketId}` renders the ticket header, ordered messages list, attachments link list. | AEP-031, ADM-011, ENT-SupportTicket, ENT-TicketMessage |
| REQ-232 | admin/tickets | support_agent OR ops_admin | Reply as an agent. | POST `/admin/tickets/{ticketId}/agent-reply` with `body` ≥ 1 char, ticket status not `closed`. Creates a `TicketMessage(author_role="agent", author_display_name=<admin.full_name>)`, writes `ADMIN_TICKET_REPLY`, refreshes ticket `last_updated_at`. Closed ticket → 409 with `TICKET_CLOSED`. | AEP-032, ADM-011, ENT-TicketMessage |
| REQ-233 | admin/tickets | support_agent OR ops_admin | Close a ticket. | POST `/admin/tickets/{ticketId}/close` → status='closed', writes `ADMIN_TICKET_CLOSED`. | AEP-033, ADM-011 |

### Admin portal — refund dispute workflow

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-240 | admin/refunds | billing_operator OR ops_admin | List pending refunds. | GET `/admin/refunds?status=pending` returns paginated table with customer, target type/id, requested amount, reason snippet, age. | AEP-040, ADM-012, ENT-Refund |
| REQ-241 | admin/refunds | billing_operator OR ops_admin | Approve a refund. | POST `/admin/refunds/{refundId}/approve` with an optional `note`. Effect: `Refund.status='approved'`, a new `Transaction(type=refund, amount=+X)` credits the wallet (or invoice line is annotated for invoice-target), `TicketMessage(author=system, body="Refund approved by <admin.full_name>")` appended to the linked ticket, ticket auto-closed if `auto_close=true`, `ADMIN_REFUND_APPROVED` audited. | AEP-041, ADM-012, ENT-Refund, ENT-Transaction, ENT-SupportTicket, ENT-TicketMessage |
| REQ-242 | admin/refunds | billing_operator OR ops_admin | Reject a refund. | POST `/admin/refunds/{refundId}/reject` with `reason`. Effect: `Refund.status='rejected'`, `TicketMessage` with rejection note, `ADMIN_REFUND_REJECTED` audited. | AEP-042, ADM-012, ENT-Refund |

### Admin portal — audit & reporting

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-250 | admin/audit | billing_operator, ops_admin, security_analyst | Browse the audit log. | GET `/admin/audit?event_type=&actor_id=&from=&to=` returns paginated audit events ordered by `timestamp` descending. Filters are optional and AND-combined. | AEP-050, ADM-013, ENT-AuditEvent |
| REQ-251 | admin/reports | billing_operator, product_manager, ops_admin, security_analyst | Reporting dashboard. | GET `/admin/reports` shows KPIs: total customers, active sessions in last 24h, purchases last 7d, refund approval rate, rate-limit hits last 24h. | AEP-051, ADM-014 |

### Admin portal — admin user management

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-260 | admin/staff | ops_admin | List, create, deactivate admin users. | GET `/admin/staff`, POST `/admin/staff/new`, POST `/admin/staff/{id}/deactivate`. Each mutation writes `ADMIN_STAFF_*` audit event. Only ops_admin. | AEP-060…AEP-062, ADM-015, ENT-AdminUser |

### Payment gateway

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-270 | gateway/payment | Customer (transparent) | Top-up through the configured driver. | Given `VULNMNO_PAYMENT_DRIVER=dev`, the existing behavior is preserved. Given `=stripe` and a valid Stripe sandbox key, a top-up of €10 results in a Stripe charge with the supplied `Idempotency-Key`; success stores `Transaction.gateway_charge_id` with the Stripe charge id. | GW-001, EP-022, ENT-Transaction |
| REQ-271 | gateway/payment | Customer (transparent) | Surface declined payments. | When Stripe returns 402 / declined, the API responds 409 with `PAYMENT_DECLINED` and `details.reason` from the Stripe error code. No transaction or balance change. | GW-001, EP-022 |
| REQ-272 | gateway/payment | Customer (transparent) | Idempotency end-to-end. | Two identical POSTs with the same `Idempotency-Key` produce one Stripe charge and identical API responses. Mismatched body with same key → 409 `IDEMPOTENCY_CONFLICT`. | GW-001 |

### Provisioning

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-280 | gateway/provisioning | Customer (transparent) | Asynchronous provisioning. | Given `VULNMNO_PROVISIONING_DRIVER=http`, when a purchase confirms, the backend POSTs to `${PROVISIONING_URL}/activate` with `{customerId, productId, purchaseId}`; on 200 marks purchase `provisioning.status=active`; on non-2xx leaves `pending` and schedules a retry. | GW-010, EP-033, ENT-Purchase |
| REQ-281 | gateway/provisioning | Customer (transparent) | Retry then fail. | After 3 failed attempts (exponential backoff 1s/5s/30s), status becomes `failed`, an `AuditEvent PROVISIONING_FAILED` is written, and the customer's wallet is auto-refunded with a `Transaction(type=refund)`. | GW-011, EP-033 |

### FCM push delivery

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-290 | gateway/push | Customer | Register device token (Phase 1 endpoint, now wired). | POST `/api/notifications/device-token` stores the token (unchanged from Phase 1). With `VULNMNO_PUSH_DRIVER=fcm`, future notifications target this token via FCM. | GW-020, EP-072, ENT-DeviceToken |
| REQ-291 | gateway/push | Customer | Receive a purchase confirmation push. | After a customer-facing `AuditEvent` is written (`PURCHASE_COMPLETED`, `PLAN_CHANGE`, `LOW_BALANCE`), the audit hook creates a `Notification` row, marks `delivery_status='queued'`, calls `push.send()`. On success → `delivery_status='sent'`, `delivered_at=now`. On failure → `delivery_status='failed'`. | GW-021, ENT-Notification |
| REQ-292 | gateway/push | Customer | Skip when prefs disabled. | If the customer's `notification_preferences.push=false`, the Notification row is created with `delivery_status='skipped'` and no send is attempted. | GW-021 |

### Rate limiting

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-300 | ops/rate-limit | any client | Per-endpoint rate limits. | `/api/auth/*`: 5/min per IP; `/api/shop/purchases` and `/api/accounts/me/topup`: 10/min per customer; `/admin/login`: 5/min per IP; default: 60/min per customer. Hits return 429 with `RATE_LIMITED` and `details.retryAfterSeconds`. | all EPs |

### Internationalization

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-310 | ops/i18n | any client | `Accept-Language` header drives localized error messages. | Given header `Accept-Language: es`, error responses' `error.message` are in Spanish (per `app/i18n.py` catalog). Default `en`. Unknown locales fall back to `en`. | all EPs |
| REQ-311 | ops/i18n | Customer | Android app supports es / en. | `values-es/strings.xml` provides Spanish translations; locale is auto-selected from device language with manual override in account settings (out of Phase 2 — auto-selection only). | SCR-007 |

### Loyalty engine

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-320 | loyalty/accrue | Customer (transparent) | Accrue points on purchase. | When `EP-033 create_purchase` confirms, points = `floor(finalPrice * tier.multiplier)` are credited to the customer's `LoyaltyAccount`; a `LoyaltyTransaction` is written with `reason='purchase'`. | LOY-001, EP-033, ENT-LoyaltyAccount, ENT-LoyaltyTransaction |
| REQ-321 | loyalty/tier | Customer (transparent) | Auto-promote on threshold. | When `LoyaltyAccount.lifetime_points` crosses a `LoyaltyTier.threshold`, `Customer.loyalty_tier` is updated and a `Notification(messageType=loyalty_tier_upgrade)` is queued. | LOY-002, ENT-LoyaltyTier, ENT-Notification |
| REQ-322 | loyalty/read | Customer | Read points balance. | GET `/api/loyalty/account` returns `{customerId, points, lifetimePoints, tier, multiplier, nextTier?, pointsToNextTier?}`. | EP-090, ENT-LoyaltyAccount |
| REQ-323 | loyalty/history | Customer | Read points history. | GET `/api/loyalty/transactions?limit=20&cursor=…` returns paginated transactions. | EP-091, ENT-LoyaltyTransaction |

### Campaign management automation

| ID | Journey | Actor | Story | Acceptance criteria | Related |
| --- | --- | --- | --- | --- | --- |
| REQ-330 | ops/campaign | system | Auto-open promotions when their `starts_at` arrives. | A lifespan-scheduled task runs hourly. Promotions with `status='draft'` and `starts_at <= now < ends_at` are flipped to `status='active'`, an `AuditEvent CAMPAIGN_OPENED` is written with `actor_id='SYSTEM'`. | LOY-* (campaign scheduler), ENT-Promotion |
| REQ-331 | ops/campaign | system | Auto-close promotions when `ends_at` passes. | Same task closes promotions with `ends_at < now`, sets `status='expired'`, audits `CAMPAIGN_CLOSED`. | ENT-Promotion |

## OUT-OF-PHASE-2

- **Loyalty points redemption** (using points to discount purchases). Phase 3.
- **Multi-factor auth for admin accounts.** Strongly recommended for ops_admin in Phase 3.
- **Supplier portal per-supplier isolation.** `supplier_admin` role exists but has zero permissions in Phase 2.
- **Push notification UI** (in-app inbox showing push history with read tracking). Phase 2 stores delivery_status but no app UI lists them yet beyond what Phase 1 already does.
- **Real FCM credentials in CI.** Tests use `DevPush`; real FCM only via docker-compose.

## Open questions

None remaining. Stage 09 will assign concrete `AEP-…` IDs and consolidate the OpenAPI delta.
