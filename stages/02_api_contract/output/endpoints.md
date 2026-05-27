# API endpoint contracts

## Scope

One row per `EP-…`. Endpoints are grouped by router (per `shared/glossary.md`) and sorted within each group by path. Schemas are defined in `openapi.yaml`; this document is the human-readable index.

Authoring workflow choice (per `contract-rules.md`): **hand-written `openapi.yaml`**. Stage 04 mirrors schemas in Pydantic and validates that the FastAPI-exported spec matches `openapi.yaml` (any divergence logged in `04_api_build/output/contract-deltas.md`).

## Inputs consumed

- `01_requirements/output/backlog.md`
- `01_requirements/output/traceability.md`
- `02_api_contract/references/contract-rules.md`
- `02_api_contract/output/auth-model.md`
- `02_api_contract/output/error-codes.md`

## Findings

### auth — `/api/auth` (REQ-001…009)

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-001 | POST | `/api/auth/login` | none | `LoginRequest` | `LoginResponse` (`TokenPair` or `OtpChallenge`) | `INVALID_CREDENTIALS`, `VALIDATION_FAILED` | §9.1 |
| EP-002 | POST | `/api/auth/logout` | bearer | — | — (204) | `UNAUTHENTICATED` | §9.1 |
| EP-003 | POST | `/api/auth/refresh` | none | `RefreshRequest` | `TokenPair` | `TOKEN_EXPIRED`, `TOKEN_REVOKED`, `VALIDATION_FAILED` | §9.1 |
| EP-004 | POST | `/api/auth/otp/verify` | none | `OtpVerifyRequest` | `TokenPair` | `OTP_INVALID`, `VALIDATION_FAILED` | §9.1 |
| EP-005 | POST | `/api/auth/password-reset/request` | none | `PasswordResetRequest` | — (204) | `VALIDATION_FAILED` | §9.1 |
| EP-006 | POST | `/api/auth/password-reset/confirm` | none | `PasswordResetConfirm` | — (204) | `OTP_INVALID`, `VALIDATION_FAILED` | §9.1 |

### customers — `/api/customers` (REQ-010, REQ-210, REQ-211)

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-010 | GET | `/api/customers/me` | bearer | — | `CustomerRead` | `UNAUTHENTICATED`, `TOKEN_EXPIRED` | §9.1 |
| EP-011 | PUT | `/api/customers/me/contact-details` | bearer | `ContactDetailsUpdate` | `CustomerRead` | `VALIDATION_FAILED` + auth errors | §9.1 |
| EP-012 | GET | `/api/customers/me/lines` | bearer | — | `Page<MobileLineRead>` | auth errors | §9.1 |
| EP-013 | GET | `/api/customers/me/sim-profile` | bearer | — | `SimProfileRead` | auth errors | §9.1 |

### accounts — `/api/accounts` (REQ-032, REQ-080…085)

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-020 | GET | `/api/accounts/me/balance` | bearer | — | `BalanceRead` | auth errors | §9.1, §9.5 |
| EP-021 | GET | `/api/accounts/me/transactions` | bearer | `?limit&cursor` | `Page<TransactionRead>` | auth errors | §9.5 |
| EP-022 | POST | `/api/accounts/me/topup` | bearer + `Idempotency-Key` | `TopupRequest` | `TransactionRead` | `VALIDATION_FAILED`, `IDEMPOTENCY_CONFLICT` | §9.2 |
| EP-023 | GET | `/api/accounts/me/invoices` | bearer | `?limit&cursor` | `Page<InvoiceSummaryRead>` | auth errors | §9.5 |
| EP-024 | GET | `/api/accounts/me/invoices/{invoiceId}` | bearer | — | `InvoiceRead` | `NOT_FOUND` | §9.5 |
| EP-025 | GET | `/api/accounts/me/invoices/{invoiceId}/download` | bearer | — | `application/pdf` | `NOT_FOUND` | §9.5 |
| EP-026 | POST | `/api/accounts/me/refunds` | bearer | `RefundRequest` | `RefundCreated` | `VALIDATION_FAILED`, `NOT_FOUND` | §9.5 |

### shop — `/api/shop` (REQ-020…031)

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-030 | GET | `/api/shop/products` | bearer | `?limit&cursor&category&featured` | `Page<ProductRead>` | auth errors | §9.1, §9.2 |
| EP-031 | GET | `/api/shop/products/{productId}` | bearer | — | `ProductRead` | `NOT_FOUND` | §9.2 |
| EP-032 | POST | `/api/shop/promotions/apply` | bearer | `ApplyPromoRequest` | `PromoApplicationRead` | `PROMO_INVALID`, `PROMO_INELIGIBLE`, `VALIDATION_FAILED` | §9.2 |
| EP-033 | POST | `/api/shop/purchases` | bearer + `Idempotency-Key` | `CreatePurchaseRequest` | `PurchaseRead` | `PROMO_INVALID`, `PROMO_INELIGIBLE`, `INSUFFICIENT_BALANCE`, `IDEMPOTENCY_CONFLICT` | §9.2 |
| EP-034 | GET | `/api/shop/purchases` | bearer | `?limit&cursor&status` | `Page<PurchaseRead>` | auth errors | §9.2 |
| EP-035 | GET | `/api/shop/purchases/{purchaseId}` | bearer | — | `PurchaseRead` | `NOT_FOUND` | §9.2 |
| EP-036 | POST | `/api/shop/purchases/{purchaseId}/cancel` | bearer | — | `PurchaseRead` | `NOT_FOUND`, `CONFLICT` | §9.2 |

### plans — `/api/plans` (REQ-040…047)

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-040 | GET | `/api/plans/current` | bearer | — | `PlanRead` | auth errors | §9.1, §9.3 |
| EP-041 | GET | `/api/plans/available` | bearer | — | `Page<PlanRead>` | auth errors | §9.3 |
| EP-042 | POST | `/api/plans/change` | bearer + `Idempotency-Key` | `PlanChangeRequest` | `PlanChangeRead` | `PLAN_INELIGIBLE`, `PLAN_CHANGE_PENDING`, `IDEMPOTENCY_CONFLICT` | §9.3 |
| EP-043 | POST | `/api/plans/change/{changeId}/cancel` | bearer | — | `PlanChangeRead` | `NOT_FOUND`, `CONFLICT` | §9.3 |
| EP-044 | POST | `/api/plans/services/add` | bearer | `ServiceToggleRequest` | `PlanRead` | `VALIDATION_FAILED`, `CONFLICT` | §9.3 |
| EP-045 | POST | `/api/plans/services/remove` | bearer | `ServiceToggleRequest` | `PlanRead` | `VALIDATION_FAILED`, `CONFLICT` | §9.3 |

### usage — `/api/usage` (REQ-060…065)

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-050 | GET | `/api/usage/calls` | bearer | `?from&to&limit&cursor` | `Page<UsageRecordRead>` | `VALIDATION_FAILED` | §9.4 |
| EP-051 | GET | `/api/usage/sms` | bearer | `?from&to&limit&cursor` | `Page<UsageRecordRead>` | `VALIDATION_FAILED` | §9.4 |
| EP-052 | GET | `/api/usage/data` | bearer | `?from&to&limit&cursor` | `Page<UsageRecordRead>` | `VALIDATION_FAILED` | §9.4 |
| EP-053 | GET | `/api/usage/roaming` | bearer | `?from&to&limit&cursor` | `Page<UsageRecordRead>` | `VALIDATION_FAILED` | §9.4 |
| EP-054 | GET | `/api/usage/export` | bearer | `?from&to&format` | `text/csv` or `application/json` | `VALIDATION_FAILED` | §9.4 |

### support — `/api/support` (REQ-100…105)

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-060 | POST | `/api/support/tickets` | bearer | `CreateTicketRequest` | `TicketRead` | `VALIDATION_FAILED` | §9.6 |
| EP-061 | GET | `/api/support/tickets` | bearer | `?limit&cursor&status` | `Page<TicketSummaryRead>` | auth errors | §9.6 |
| EP-062 | GET | `/api/support/tickets/{ticketId}` | bearer | — | `TicketRead` | `NOT_FOUND` | §9.6 |
| EP-063 | POST | `/api/support/tickets/{ticketId}/messages` | bearer | `CreateMessageRequest` | `TicketMessageRead` | `NOT_FOUND`, `TICKET_CLOSED` | §9.6 |
| EP-064 | POST | `/api/support/tickets/{ticketId}/attachments` | bearer | `multipart/form-data` | `TicketAttachmentRead` | `NOT_FOUND`, `TICKET_CLOSED`, `VALIDATION_FAILED` | §9.6 |
| EP-065 | POST | `/api/support/tickets/{ticketId}/close` | bearer | — | `TicketRead` | `NOT_FOUND`, `CONFLICT` | §9.6 |

### notifications — `/api/notifications` (REQ-012, REQ-212)

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-070 | GET | `/api/notifications` | bearer | `?limit&cursor` | `Page<NotificationRead>` | auth errors | cross |
| EP-071 | POST | `/api/notifications/preferences` | bearer | `NotificationPreferencesUpdate` | `NotificationPreferences` | `VALIDATION_FAILED` | cross |
| EP-072 | POST | `/api/notifications/device-token` | bearer | `DeviceTokenRegister` | — (204) | `VALIDATION_FAILED` | §9.1 |

### Resolutions of stage-01 Open questions

1. **OTP enrollment surface.** OTP enrollment is a property of the seeded `Customer` row (`otp_enrolled: bool`). No enrollment endpoint in phase 1.
2. **Refund settlement.** `EP-026 POST /api/accounts/me/refunds` returns `202` with `{refundId, status: "pending", ticketId}`. The refund is also represented as a `SupportTicket` of topic `Billing` so the customer can track it via §9.6. No `GET /refunds/{id}` in phase 1.
3. **Invoice line items.** Separate entity (`InvoiceLineItem`). The `InvoiceRead` schema embeds them inline as an array. Stage 03 owns the DB representation.
4. **Provisioning visibility.** `PurchaseRead.provisioning` is a sub-object `{status: "pending" | "active" | "failed", activatedAt?: datetime}`. Phase 1 simulates `status = "active"` immediately on a confirmed purchase.
5. **Attachment storage.** Filesystem under `output/backend/uploads/{customerId}/{ticketId}/`. Stage 03 declares the column, stage 04 implements the writer. Max size 10 MB enforced at the FastAPI layer.
6. **Device-token stub.** `EP-072` returns `204 No Content`. The token is stored against the customer (used as the recipient address of stored `Notification` rows). No FCM call in phase 1.
7. **Agent-side ticket replies.** Out of phase 1. `TicketMessageRead.author.role` is always `"customer"`; agent-authored messages can be seeded for tests but no endpoint creates them.

## Open questions

None remaining for stage 02. All seven stage-01 questions are resolved above.
