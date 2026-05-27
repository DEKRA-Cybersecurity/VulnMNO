# Traceability matrix

## Scope

One row per `REQ-…` in `backlog.md`, mapping it to candidate §12 endpoints and §11 entities. Stage 02 consumes this matrix to assign `EP-…` IDs and decide endpoint splits/merges. Stage 03 uses the entity column to plan the schema.

## Inputs consumed

- `stages/01_requirements/output/backlog.md`
- `docs/VulnMNO.md` §11 (data model) and §12 (endpoints).

## Findings

| REQ-ID | Journey | §12 endpoint(s) | §11 entities |
| --- | --- | --- | --- |
| REQ-001 | §9.1 | `POST /api/auth/login` | Customer, MobileLine |
| REQ-002 | §9.1 | `POST /api/auth/login` | Customer |
| REQ-003 | §9.1 | `POST /api/auth/otp/verify` | Customer |
| REQ-004 | §9.1 | `POST /api/auth/login` | Customer |
| REQ-005 | §9.1 | `POST /api/auth/otp/verify` | Customer |
| REQ-006 | §9.1 | `POST /api/auth/refresh` | Customer |
| REQ-007 | §9.1 | `POST /api/auth/logout` | Customer |
| REQ-008 | §9.1 | `POST /api/auth/password-reset/request` | Customer |
| REQ-009 | §9.1 | `POST /api/auth/password-reset/confirm` | Customer |
| REQ-010 | §9.1 | `GET /api/customers/me` | Customer |
| REQ-011 | §9.1 | `GET /api/customers/me`, `GET /api/accounts/me/balance`, `GET /api/plans/current`, `GET /api/shop/products` | Customer, Account, Balance, Plan, Product |
| REQ-012 | §9.1 | `POST /api/notifications/device-token` | Customer, Notification |
| REQ-020 | §9.2 | `GET /api/shop/products` | Product |
| REQ-021 | §9.2 | `GET /api/shop/products/{productId}` | Product, Plan |
| REQ-022 | §9.2 | `POST /api/shop/promotions/apply` | Promotion, Coupon, Product |
| REQ-023 | §9.2 | `POST /api/shop/promotions/apply` | Coupon |
| REQ-024 | §9.2 | `POST /api/shop/promotions/apply` | Promotion |
| REQ-025 | §9.2 | `POST /api/shop/purchases` | Purchase, Promotion, Transaction |
| REQ-026 | §9.2 | `POST /api/shop/purchases` | Purchase, Balance |
| REQ-027 | §9.2 | `POST /api/shop/purchases` | Balance, Transaction, AuditEvent |
| REQ-028 | §9.2 | `POST /api/shop/purchases` | Purchase |
| REQ-029 | §9.2 | `GET /api/shop/purchases` | Purchase |
| REQ-030 | §9.2 | `GET /api/shop/purchases/{purchaseId}` | Purchase |
| REQ-031 | §9.2 | `POST /api/shop/purchases/{purchaseId}/cancel` | Purchase, Transaction |
| REQ-032 | §9.2 | `POST /api/accounts/me/topup` | Balance, Transaction |
| REQ-040 | §9.3 | `GET /api/plans/current` | Plan |
| REQ-041 | §9.3 | `GET /api/plans/available` | Plan, Customer |
| REQ-042 | §9.3 | `POST /api/plans/change` | Plan, AuditEvent |
| REQ-043 | §9.3 | `POST /api/plans/change` | Plan |
| REQ-044 | §9.3 | `POST /api/plans/change` | Plan |
| REQ-045 | §9.3 | `POST /api/plans/change/{changeId}/cancel` | Plan |
| REQ-046 | §9.3 | `POST /api/plans/services/add` | Plan, MobileLine |
| REQ-047 | §9.3 | `POST /api/plans/services/remove` | Plan, MobileLine |
| REQ-060 | §9.4 | `GET /api/usage/calls` | UsageRecord, MobileLine |
| REQ-061 | §9.4 | `GET /api/usage/sms` | UsageRecord |
| REQ-062 | §9.4 | `GET /api/usage/data` | UsageRecord |
| REQ-063 | §9.4 | `GET /api/usage/roaming` | UsageRecord |
| REQ-064 | §9.4 | `GET /api/usage/calls`, `GET /api/usage/sms`, `GET /api/usage/data`, `GET /api/usage/roaming` | UsageRecord |
| REQ-065 | §9.4 | `GET /api/usage/export` | UsageRecord |
| REQ-080 | §9.5 | `GET /api/accounts/me/invoices` | Invoice |
| REQ-081 | §9.5 | `GET /api/accounts/me/invoices/{invoiceId}` | Invoice |
| REQ-082 | §9.5 | `GET /api/accounts/me/invoices/{invoiceId}/download` | Invoice |
| REQ-083 | §9.5 | `GET /api/accounts/me/transactions` | Transaction |
| REQ-084 | §9.5 | `POST /api/accounts/me/refunds` | Transaction, SupportTicket |
| REQ-085 | §9.5 | `GET /api/accounts/me/balance` | Balance |
| REQ-100 | §9.6 | `POST /api/support/tickets` | SupportTicket, AuditEvent |
| REQ-101 | §9.6 | `GET /api/support/tickets` | SupportTicket |
| REQ-102 | §9.6 | `GET /api/support/tickets/{ticketId}` | SupportTicket, TicketMessage |
| REQ-103 | §9.6 | `POST /api/support/tickets/{ticketId}/messages` | TicketMessage, SupportTicket |
| REQ-104 | §9.6 | `POST /api/support/tickets/{ticketId}/attachments` | TicketMessage |
| REQ-105 | §9.6 | `POST /api/support/tickets/{ticketId}/close` | SupportTicket |
| REQ-200 | cross | all `/api/*` non-auth | — |
| REQ-201 | cross | all protected | — |
| REQ-202 | cross | all `/me` | Customer |
| REQ-203 | cross | all by-ID | — |
| REQ-204 | cross | all | — |
| REQ-205 | cross | all list | — |
| REQ-206 | cross | all money | Balance, Transaction, Purchase, Invoice |
| REQ-207 | cross | all datetime | — |
| REQ-208 | cross | all | all |
| REQ-209 | cross | login/purchase/plan/refund/ticket | AuditEvent |
| REQ-210 | §9.1 | `PUT /api/customers/me/contact-details` | Customer |
| REQ-211 | §9.1 | `GET /api/customers/me/lines`, `GET /api/customers/me/sim-profile` | MobileLine, SIMProfile |
| REQ-212 | §9.1 | `GET /api/notifications`, `POST /api/notifications/preferences` | Notification, Customer |

## Coverage summary

- **§12 endpoints covered:** all 38 endpoints listed in §12.1–§12.8 have at least one `REQ-…`.
- **§11 entities covered:** Customer, Account, MobileLine, SIMProfile, Balance, Product, Plan, Promotion, Coupon, Purchase, Transaction, Invoice, UsageRecord, SupportTicket, Notification, AuditEvent. Additionally `TicketMessage` is introduced (not in §11 but required by §12.7) — flagged as Open question in `backlog.md`.
- **Journeys covered:** §9.1 (REQ-001…012, REQ-210…212), §9.2 (REQ-020…032), §9.3 (REQ-040…047), §9.4 (REQ-060…065), §9.5 (REQ-080…085), §9.6 (REQ-100…105), Cross-cutting (REQ-200…209).

## Open questions

(Inherited from `backlog.md` — listed here for stage 02 convenience.)

1. OTP enrollment surface (REQ-002, REQ-003).
2. Refund settlement endpoint inclusion (REQ-084).
3. `InvoiceLineItem` as separate entity vs JSON (REQ-081).
4. Provisioning visibility on purchase detail (REQ-027).
5. Attachment storage location (REQ-104).
6. Notification delivery stub status code (REQ-012).
7. Agent-side ticket replies (§9.6) — out of phase 1, confirm.
