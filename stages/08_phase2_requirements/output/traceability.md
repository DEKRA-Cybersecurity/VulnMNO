# Phase 2 traceability matrix

## Scope

One row per `REQ-2…`/`REQ-3…` mapping it to candidate Phase-2 endpoint IDs (`AEP-` for admin HTML, `EP-` for JSON API, `GW-` for gateway adapter operations), entities (`ENT-`), screens (`ADM-` for admin, `SCR-` for mobile). Stage 09 finalizes the IDs.

## Inputs consumed

- `output/backlog.md`
- `output/admin-rbac-matrix.md`

## Findings

| REQ-ID | AEP / EP / GW | ENT | Screen |
| --- | --- | --- | --- |
| REQ-200 admin login | AEP-001 GET /admin/login, AEP-002 POST /admin/login | AdminUser, AuditEvent | ADM-001 |
| REQ-201 invalid creds | AEP-001 / AEP-002 | AuditEvent | ADM-001 |
| REQ-202 admin logout | AEP-003 POST /admin/logout | AdminUser | (no screen — header link) |
| REQ-203 session-expired redirect | every protected AEP- | — | — |
| REQ-204 CSRF | every admin write AEP- | — | — |
| REQ-210 customer search | AEP-010 GET /admin/customers | Customer | ADM-003 |
| REQ-211 customer detail | AEP-011 GET /admin/customers/{id}, AEP-012 /{id}/transactions, AEP-013 /{id}/purchases | Customer, Balance, Transaction, Purchase, Plan, SupportTicket | ADM-004 |
| REQ-212 balance adjust | AEP-014 POST /admin/customers/{id}/balance-adjust | Balance, Transaction, AuditEvent | ADM-005 |
| REQ-220 plan CRUD | AEP-020 GET /admin/plans, AEP-021 POST /admin/plans/new, AEP-022 POST /admin/plans/{id}/edit, AEP-023 POST /admin/plans/{id}/archive | Plan, AuditEvent | ADM-006, ADM-007 |
| REQ-221 promotion CRUD | AEP-024…AEP-027 over /admin/promotions/* | Promotion, AuditEvent | ADM-008 |
| REQ-222 coupon batch gen | AEP-028 POST /admin/promotions/{id}/coupons/generate | Coupon | ADM-009 |
| REQ-230 ticket list | AEP-030 GET /admin/tickets | SupportTicket | ADM-010 |
| REQ-231 ticket detail | AEP-031 GET /admin/tickets/{id} | SupportTicket, TicketMessage | ADM-011 |
| REQ-232 agent reply | AEP-032 POST /admin/tickets/{id}/agent-reply | TicketMessage, AuditEvent | ADM-011 |
| REQ-233 close ticket | AEP-033 POST /admin/tickets/{id}/close | SupportTicket, AuditEvent | ADM-011 |
| REQ-240 refund list | AEP-040 GET /admin/refunds | Refund | ADM-012 |
| REQ-241 refund approve | AEP-041 POST /admin/refunds/{id}/approve | Refund, Transaction, TicketMessage, AuditEvent | ADM-012 |
| REQ-242 refund reject | AEP-042 POST /admin/refunds/{id}/reject | Refund, TicketMessage, AuditEvent | ADM-012 |
| REQ-250 audit log viewer | AEP-050 GET /admin/audit | AuditEvent | ADM-013 |
| REQ-251 reports | AEP-051 GET /admin/reports | (read-only views) | ADM-014 |
| REQ-260 admin users CRUD | AEP-060 GET /admin/staff, AEP-061 POST /admin/staff/new, AEP-062 POST /admin/staff/{id}/deactivate | AdminUser, AuditEvent | ADM-015 |
| REQ-270 payment driver switch | GW-001 PaymentGateway.charge | Transaction (gateway_charge_id field) | — |
| REQ-271 payment declined | GW-001 | — | — |
| REQ-272 payment idempotency | GW-001 | IdempotencyKey | — |
| REQ-280 provisioning async | GW-010 ProvisioningClient.activate_bundle | Purchase | — |
| REQ-281 provisioning retry/fail | GW-011 ProvisioningClient (background) | Purchase, AuditEvent, Transaction | — |
| REQ-290 device token wired | GW-020 PushDelivery (no-op for token registration) | DeviceToken | — |
| REQ-291 push on audit | GW-021 PushDelivery.send | Notification | — |
| REQ-292 push prefs skip | GW-021 | Notification (delivery_status=skipped) | — |
| REQ-300 rate limit | every EP-/AEP- | — | — |
| REQ-310 backend i18n | every EP- error path | — | — |
| REQ-311 mobile i18n | (resource files) | — | SCR-007 |
| REQ-320 loyalty accrue | hook in EP-033 | LoyaltyAccount, LoyaltyTransaction | — |
| REQ-321 loyalty tier upgrade | (internal service) | LoyaltyTier, Customer, Notification | — |
| REQ-322 loyalty read | EP-090 GET /api/loyalty/account | LoyaltyAccount | SCR-007 (extension) |
| REQ-323 loyalty history | EP-091 GET /api/loyalty/transactions | LoyaltyTransaction | SCR-007 (extension) |
| REQ-330 campaign auto-open | (lifespan scheduler) | Promotion, AuditEvent | — |
| REQ-331 campaign auto-close | (lifespan scheduler) | Promotion, AuditEvent | — |

## Coverage summary

- **Admin AEP-IDs:** AEP-001 … AEP-062, 28 endpoints total.
- **New customer API EP-IDs:** EP-090 (loyalty account), EP-091 (loyalty transactions) — 2 new public endpoints.
- **Gateway operations:** GW-001 (payment), GW-010/GW-011 (provisioning), GW-020/GW-021 (push) — 5 abstract ops.
- **New entities (Stage 10):** AdminUser, LoyaltyAccount, LoyaltyTransaction, LoyaltyTier. Extensions: Notification.delivery_status, Notification.delivered_at, Transaction.gateway_charge_id.

## Open questions

None for Stage 08. Stage 09 consolidates the OpenAPI delta and finalizes the AEP- ↔ template route mapping.
