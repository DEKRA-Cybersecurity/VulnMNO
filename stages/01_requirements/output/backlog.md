# Phase 1 backlog

## Scope

Functional backlog for VulnMNO phase 1 derived from `docs/VulnMNO.md` §9.1–§9.6 (six customer journeys) plus cross-cutting requirements implied by §7.1, §12, §13. One row per acceptance criterion using **Given / When / Then**. Out-of-phase items are marked with `OUT-OF-PHASE-1` at the bottom.

## Inputs consumed

- `docs/VulnMNO.md` §2, §4, §7.1, §9.1–§9.6, §10, §11, §12, §13.
- `setup/questionnaire.md` — phase scope confirmation (all journeys §9.1–§9.6 in scope).
- `shared/glossary.md` — canonical names.
- `shared/source-pointer.md` — section index.
- `_config/conventions.md` — `REQ-` IDs and table shape.
- `stages/01_requirements/references/requirements-template.md` — entry rules.

## Findings

### §9.1 Login and account overview

| ID | Journey | Actor | Story | Acceptance criteria | Related EP / ENT |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | §9.1 | Customer | Authenticate with phone + password when not OTP-enrolled. | Given a registered MSISDN and correct password and the customer is not OTP-enrolled, when `POST /api/auth/login` is called with `{msisdn, password}`, then the response is `200` containing an access token (JWT) and a refresh token. | `POST /api/auth/login` / Customer, MobileLine |
| REQ-002 | §9.1 | Customer | Authenticate with phone + password + OTP when OTP-enrolled. | Given a registered MSISDN and correct password and the customer is OTP-enrolled, when `POST /api/auth/login` is called, then the response is `200` with `{challenge: "OTP", challengeToken}` and no tokens are issued yet. | `POST /api/auth/login` / Customer |
| REQ-003 | §9.1 | Customer | Complete OTP challenge to receive tokens. | Given a valid `challengeToken` issued ≤ 5 minutes ago and the correct OTP code, when `POST /api/auth/otp/verify` is called with `{challengeToken, code}`, then the response is `200` with access and refresh tokens. | `POST /api/auth/otp/verify` / Customer |
| REQ-004 | §9.1 | Customer | Receive a clear error on wrong credentials. | Given any registered MSISDN and an incorrect password, when `POST /api/auth/login` is called, then the response is `401` with `error.code = INVALID_CREDENTIALS` and no information about whether the MSISDN exists. | `POST /api/auth/login` / Customer |
| REQ-005 | §9.1 | Customer | Reject expired OTP. | Given a `challengeToken` issued more than 5 minutes ago, when `POST /api/auth/otp/verify` is called, then the response is `401` with `error.code = OTP_INVALID`. | `POST /api/auth/otp/verify` / Customer |
| REQ-006 | §9.1 | Customer | Refresh an active session. | Given a non-revoked refresh token, when `POST /api/auth/refresh` is called with the refresh token, then a new access token and a new refresh token are returned and the old refresh token is invalidated. | `POST /api/auth/refresh` / Customer |
| REQ-007 | §9.1 | Customer | End an active session. | Given a valid bearer token, when `POST /api/auth/logout` is called, then the refresh token associated with the session is revoked and subsequent refresh attempts return `401`. | `POST /api/auth/logout` / Customer |
| REQ-008 | §9.1 | Customer | Request a password reset by SMS. | Given a registered MSISDN, when `POST /api/auth/password-reset/request` is called with `{msisdn}`, then the response is `204` and a one-time reset code is sent to that MSISDN via simulated SMS (logged, not delivered in phase 1). | `POST /api/auth/password-reset/request` / Customer |
| REQ-009 | §9.1 | Customer | Complete a password reset. | Given a valid reset code, when `POST /api/auth/password-reset/confirm` is called with `{msisdn, code, newPassword}`, then the password is updated and all existing refresh tokens for the customer are revoked. | `POST /api/auth/password-reset/confirm` / Customer |
| REQ-010 | §9.1 | Customer | Retrieve own profile after authentication. | Given a valid bearer token for `CUST-X`, when `GET /api/customers/me` is called, then the response is `200` and matches the §13.1 example payload shape (`customerId, name, email, primaryMsisdn, accountType, status, loyaltyTier`). | `GET /api/customers/me` / Customer |
| REQ-011 | §9.1 | Customer | See balance, plan, recent usage and offers on the home dashboard. | Given a valid bearer token, when the Home screen loads, then it has issued `GET /api/customers/me`, `GET /api/accounts/me/balance`, `GET /api/plans/current` and `GET /api/shop/products?featured=true` and renders one section per result. | `GET` × 4 / Customer, Account, Balance, Plan, Product |
| REQ-012 | §9.1 | Customer | Register a device for the session. | Given a valid bearer token, when `POST /api/notifications/device-token` is called with `{token, platform: "android"}`, then the token is stored against the customer and used as the target of future notifications (delivery itself is stubbed in phase 1). | `POST /api/notifications/device-token` / Customer, Notification |

### §9.2 Purchase of a data bundle

| ID | Journey | Actor | Story | Acceptance criteria | Related EP / ENT |
| --- | --- | --- | --- | --- | --- |
| REQ-020 | §9.2 | Customer | Browse the product catalog. | Given a valid bearer token, when `GET /api/shop/products?limit=20` is called, then the response is `200` with a cursor-paginated list of products matching the §13.3 example payload shape. | `GET /api/shop/products` / Product |
| REQ-021 | §9.2 | Customer | View product detail. | Given a known `productId`, when `GET /api/shop/products/{productId}` is called, then the response includes `productId, name, category, description, price, currency, validityDays, eligiblePlans`. | `GET /api/shop/products/{productId}` / Product, Plan |
| REQ-022 | §9.2 | Customer | Get final price after applying a promo. | Given a valid `promoCode` and a `productId` the customer is eligible for, when `POST /api/shop/promotions/apply` is called with `{productId, promoCode}`, then the response matches the §13.4 example payload shape (`promotionId, description, originalPrice, discountAmount, finalPrice, currency`) and `finalPrice ≥ 0`. | `POST /api/shop/promotions/apply` / Promotion, Coupon, Product |
| REQ-023 | §9.2 | Customer | See a clear error on an unknown promo code. | Given an unknown `promoCode`, when `POST /api/shop/promotions/apply` is called, then the response is `400` with `error.code = PROMO_INVALID`. | `POST /api/shop/promotions/apply` / Coupon |
| REQ-024 | §9.2 | Customer | See a clear error when not eligible for a promo. | Given a known `promoCode` whose eligibility rules exclude this customer (e.g. account type, prior usage), when `POST /api/shop/promotions/apply` is called, then the response is `400` with `error.code = PROMO_INELIGIBLE` and `details.reason` naming the eligibility rule that failed. | `POST /api/shop/promotions/apply` / Promotion |
| REQ-025 | §9.2 | Customer | Create a purchase with an applied promo. | Given a valid `productId`, an applied `promoCode` and sufficient wallet balance, when `POST /api/shop/purchases` is called with `{productId, promoCode}`, then the response is `201` with a `Purchase` payload matching §13.5 (`purchaseId, customerId, productId, status: "confirmed", finalPrice, currency, createdAt`). | `POST /api/shop/purchases` / Purchase, Promotion, Transaction |
| REQ-026 | §9.2 | Customer | Refuse a purchase when balance is insufficient. | Given a confirmed final price exceeding the wallet balance and no other payment method, when `POST /api/shop/purchases` is called, then the response is `409` with `error.code = INSUFFICIENT_BALANCE` and no `Purchase` row is created. | `POST /api/shop/purchases` / Purchase, Balance |
| REQ-027 | §9.2 | Customer | Have wallet debited and a transaction recorded on a successful purchase. | Given a successful `POST /api/shop/purchases`, when the response returns `201`, then the customer's `Balance.amount` has decreased by `finalPrice`, a new `Transaction` row exists with `type = "purchase"` and `amount = -finalPrice`, and an `AuditEvent` of type `PURCHASE_COMPLETED` has been written. | `POST /api/shop/purchases` / Balance, Transaction, AuditEvent |
| REQ-028 | §9.2 | Customer | Submit purchases idempotently. | Given an `Idempotency-Key` header, when `POST /api/shop/purchases` is called twice with the same key within 24h, then only one `Purchase` row exists and the second call returns the same response body as the first. | `POST /api/shop/purchases` / Purchase |
| REQ-029 | §9.2 | Customer | Browse purchase history. | Given a valid bearer token, when `GET /api/shop/purchases?limit=20` is called, then the response is a cursor-paginated list of the caller's purchases sorted by `createdAt` descending. | `GET /api/shop/purchases` / Purchase |
| REQ-030 | §9.2 | Customer | View a single purchase. | Given a `purchaseId` owned by the caller, when `GET /api/shop/purchases/{purchaseId}` is called, then the response is `200` with the full purchase payload. Given a `purchaseId` not owned by the caller, the response is `404 NOT_FOUND` (no existence leak). | `GET /api/shop/purchases/{purchaseId}` / Purchase |
| REQ-031 | §9.2 | Customer | Cancel a purchase that is still cancellable. | Given a `purchaseId` whose status is `confirmed` and whose product has not been provisioned, when `POST /api/shop/purchases/{purchaseId}/cancel` is called, then status transitions to `cancelled`, a `Transaction` of type `refund` is created restoring the wallet, and `error.code = CONFLICT` is returned if the purchase is no longer cancellable. | `POST /api/shop/purchases/{purchaseId}/cancel` / Purchase, Transaction |
| REQ-032 | §9.2 | Customer | Top-up the prepaid wallet. | Given a valid bearer token and a positive `amount`, when `POST /api/accounts/me/topup` is called with `{amount, currency: "EUR"}` and an `Idempotency-Key`, then the response is `201` with the new balance, a `Transaction` of type `topup` is created, and replays with the same key return the same body. | `POST /api/accounts/me/topup` / Balance, Transaction |

### §9.3 Plan change

| ID | Journey | Actor | Story | Acceptance criteria | Related EP / ENT |
| --- | --- | --- | --- | --- | --- |
| REQ-040 | §9.3 | Customer | View current plan. | Given a valid bearer token, when `GET /api/plans/current` is called, then the response is `200` with `{planId, name, monthlyPrice, currency, dataLimit, voiceLimit, validFrom}` for the active plan. | `GET /api/plans/current` / Plan |
| REQ-041 | §9.3 | Customer | List plans available to the customer. | Given a valid bearer token, when `GET /api/plans/available` is called, then the response is `200` with a list of plans filtered by the customer's `accountType` and loyalty eligibility. | `GET /api/plans/available` / Plan, Customer |
| REQ-042 | §9.3 | Customer | Change plan immediately. | Given an eligible `planId` distinct from the current one, when `POST /api/plans/change` is called with `{planId, mode: "immediate"}`, then the response is `200`, the active plan is updated, an `AuditEvent` of type `PLAN_CHANGE` is written and the new plan is visible in the next `GET /api/plans/current`. | `POST /api/plans/change` / Plan, AuditEvent |
| REQ-043 | §9.3 | Customer | Schedule a plan change. | Given an eligible `planId` and `mode: "scheduled"` with a future `effectiveDate`, when `POST /api/plans/change` is called, then the response is `202` with `{changeId, status: "pending", effectiveDate}` and the change is applied on `effectiveDate`. | `POST /api/plans/change` / Plan |
| REQ-044 | §9.3 | Customer | See a clear error when ineligible for a plan. | Given a `planId` whose eligibility rules exclude this customer, when `POST /api/plans/change` is called, then the response is `400` with `error.code = PLAN_INELIGIBLE` and `details.reason` naming the rule. | `POST /api/plans/change` / Plan |
| REQ-045 | §9.3 | Customer | Cancel a pending plan change. | Given a `changeId` whose status is `pending`, when `POST /api/plans/change/{changeId}/cancel` is called, then status becomes `cancelled` and the active plan is unchanged. Given a non-pending change, the response is `409` with `error.code = CONFLICT`. | `POST /api/plans/change/{changeId}/cancel` / Plan |
| REQ-046 | §9.3 | Customer | Add an optional service. | Given a valid bearer token and a `serviceId` available on the current plan, when `POST /api/plans/services/add` is called, then the response is `200`, the service is active on the customer's line and is reflected in `GET /api/plans/current`. | `POST /api/plans/services/add` / Plan, MobileLine |
| REQ-047 | §9.3 | Customer | Remove an optional service. | Given a `serviceId` currently active on the customer's line, when `POST /api/plans/services/remove` is called, then the response is `200` and the service is no longer active. | `POST /api/plans/services/remove` / Plan, MobileLine |

### §9.4 Usage review

| ID | Journey | Actor | Story | Acceptance criteria | Related EP / ENT |
| --- | --- | --- | --- | --- | --- |
| REQ-060 | §9.4 | Customer | View call records. | Given a valid bearer token and a default date range (last 30 days), when `GET /api/usage/calls?limit=20` is called, then the response is a cursor-paginated list of calls matching the §13.6 example payload shape (`usageId, lineId, type, direction, destination, startedAt, durationSeconds, cost, currency`). | `GET /api/usage/calls` / UsageRecord, MobileLine |
| REQ-061 | §9.4 | Customer | View SMS usage. | Given a valid bearer token, when `GET /api/usage/sms?limit=20` is called, then the response is a cursor-paginated list of SMS usage records. | `GET /api/usage/sms` / UsageRecord |
| REQ-062 | §9.4 | Customer | View data usage. | Given a valid bearer token, when `GET /api/usage/data?limit=20` is called, then the response is a cursor-paginated list of data sessions with `volumeMegabytes` and `cost`. | `GET /api/usage/data` / UsageRecord |
| REQ-063 | §9.4 | Customer | View roaming usage. | Given a valid bearer token, when `GET /api/usage/roaming?limit=20` is called, then the response is a cursor-paginated list of roaming usage with `country` and `networkType` fields populated. | `GET /api/usage/roaming` / UsageRecord |
| REQ-064 | §9.4 | Customer | Filter usage by date range. | Given query parameters `from=2026-05-01&to=2026-05-31`, when any of the `GET /api/usage/*` endpoints is called, then only records with `startedAt` inside the inclusive range are returned. Invalid ranges (`from > to`) return `400 VALIDATION_FAILED`. | `GET /api/usage/*` / UsageRecord |
| REQ-065 | §9.4 | Customer | Export a usage summary. | Given a valid bearer token and a date range, when `GET /api/usage/export?from=…&to=…&format=csv` is called, then the response is `200` with `Content-Type: text/csv` and one row per usage record, summed by `type`. `format=json` returns the same data as JSON. | `GET /api/usage/export` / UsageRecord |

### §9.5 Invoice review

| ID | Journey | Actor | Story | Acceptance criteria | Related EP / ENT |
| --- | --- | --- | --- | --- | --- |
| REQ-080 | §9.5 | Customer | List invoices. | Given a valid bearer token, when `GET /api/accounts/me/invoices?limit=20` is called, then the response is a cursor-paginated list of invoices with `invoiceId, accountId, period, totalAmount, currency, status, issuedAt`. | `GET /api/accounts/me/invoices` / Invoice |
| REQ-081 | §9.5 | Customer | View invoice detail. | Given an `invoiceId` owned by the caller, when `GET /api/accounts/me/invoices/{invoiceId}` is called, then the response includes the line-item breakdown (one row per service or product billed in the period). Foreign `invoiceId` returns `404 NOT_FOUND`. | `GET /api/accounts/me/invoices/{invoiceId}` / Invoice |
| REQ-082 | §9.5 | Customer | Download the invoice PDF. | Given an `invoiceId` owned by the caller, when `GET /api/accounts/me/invoices/{invoiceId}/download` is called, then the response is `200` with `Content-Type: application/pdf` and a non-empty body. The PDF can be deterministic (template-rendered) in phase 1. | `GET /api/accounts/me/invoices/{invoiceId}/download` / Invoice |
| REQ-083 | §9.5 | Customer | View transaction history. | Given a valid bearer token, when `GET /api/accounts/me/transactions?limit=20` is called, then the response is a cursor-paginated list of `Transaction` rows (top-ups, purchases, refunds) sorted by `timestamp` descending. | `GET /api/accounts/me/transactions` / Transaction |
| REQ-084 | §9.5 | Customer | Request a refund. | Given a `purchaseId` or `invoiceId` and a reason, when `POST /api/accounts/me/refunds` is called with `{targetType, targetId, reason}`, then the response is `202` with `{refundId, status: "pending"}`. Refund processing itself is async and out of phase 1's UI; only ticket creation is required here. | `POST /api/accounts/me/refunds` / Transaction, SupportTicket |
| REQ-085 | §9.5 | Customer | See the current balance. | Given a valid bearer token, when `GET /api/accounts/me/balance` is called, then the response matches the §13.2 example payload shape (`accountId, balance, currency, lastUpdated`). | `GET /api/accounts/me/balance` / Balance |

### §9.6 Support request

| ID | Journey | Actor | Story | Acceptance criteria | Related EP / ENT |
| --- | --- | --- | --- | --- | --- |
| REQ-100 | §9.6 | Customer | Create a support ticket. | Given a valid bearer token and `{topic, description}`, when `POST /api/support/tickets` is called, then the response is `201` with `{ticketId, customerId, topic, status: "open", createdAt}` and an `AuditEvent` of type `SUPPORT_TICKET_CREATED` is written. | `POST /api/support/tickets` / SupportTicket, AuditEvent |
| REQ-101 | §9.6 | Customer | List my tickets. | Given a valid bearer token, when `GET /api/support/tickets?limit=20` is called, then the response is a cursor-paginated list of the caller's tickets sorted by `createdAt` descending. | `GET /api/support/tickets` / SupportTicket |
| REQ-102 | §9.6 | Customer | View ticket detail. | Given a `ticketId` owned by the caller, when `GET /api/support/tickets/{ticketId}` is called, then the response includes the ticket and its ordered list of messages. Foreign tickets return `404 NOT_FOUND`. | `GET /api/support/tickets/{ticketId}` / SupportTicket, TicketMessage |
| REQ-103 | §9.6 | Customer | Add a message to an open ticket. | Given an open `ticketId` owned by the caller and a non-empty `body`, when `POST /api/support/tickets/{ticketId}/messages` is called, then the response is `201` with the created message. Closed tickets return `409` with `error.code = TICKET_CLOSED`. | `POST /api/support/tickets/{ticketId}/messages` / TicketMessage, SupportTicket |
| REQ-104 | §9.6 | Customer | Upload an attachment to a ticket. | Given an open `ticketId` owned by the caller and a multipart payload ≤ 10 MB, when `POST /api/support/tickets/{ticketId}/attachments` is called, then the response is `201` with `{attachmentId, filename, sizeBytes, contentType}`. Files > 10 MB return `400 VALIDATION_FAILED`. | `POST /api/support/tickets/{ticketId}/attachments` / TicketMessage |
| REQ-105 | §9.6 | Customer | Close a ticket. | Given an open `ticketId` owned by the caller, when `POST /api/support/tickets/{ticketId}/close` is called, then status becomes `closed` and subsequent message attempts return `TICKET_CLOSED`. | `POST /api/support/tickets/{ticketId}/close` / SupportTicket |

### Cross-cutting

| ID | Journey | Actor | Story | Acceptance criteria | Related EP / ENT |
| --- | --- | --- | --- | --- | --- |
| REQ-200 | cross | system | Every non-auth endpoint requires a valid bearer JWT. | Given any request to `/api/*` other than `/api/auth/*`, when the `Authorization` header is missing or malformed, then the response is `401` with `error.code = UNAUTHENTICATED`. | all `/api/*` (non-auth) / — |
| REQ-201 | cross | system | Expired access tokens are rejected cleanly. | Given an `Authorization` header carrying an expired JWT, when any protected endpoint is called, then the response is `401` with `error.code = TOKEN_EXPIRED`. | all protected EPs / — |
| REQ-202 | cross | system | `me` resolves only from the access token. | Given any endpoint containing `/me`, when the request is processed, then the customer scope is derived from the JWT `sub` claim, never from a path or query parameter. | all `/me` EPs / Customer |
| REQ-203 | cross | system | Cross-customer access returns 404. | Given a resource owned by a different customer, when the caller addresses it by ID (e.g. `purchaseId`, `invoiceId`, `ticketId`), then the response is `404 NOT_FOUND` — never `403` — to avoid existence leaks. | all by-ID EPs / — |
| REQ-204 | cross | system | All error responses use the single envelope. | Given any non-2xx response from any endpoint, when the body is parsed, then it matches `{error: {code, message, details?}}` and `code` is a member of the master enum maintained in `02_api_contract/output/error-codes.md`. | all EPs / — |
| REQ-205 | cross | system | List endpoints are cursor-paginated. | Given any `GET` endpoint that returns a collection, when called with `?limit=N&cursor=…`, then the response is `{items, nextCursor}` with `nextCursor` null on the last page; default `limit = 20`, max `100`. | all list EPs / — |
| REQ-206 | cross | system | Money is EUR with two decimal places. | Given any payload field representing money, when serialized, then the value is a JSON number with exactly two decimal digits and any companion `currency` field equals `"EUR"`. | all money EPs / Balance, Transaction, Purchase, Invoice |
| REQ-207 | cross | system | Datetimes are ISO 8601 UTC. | Given any payload field representing a moment in time, when serialized, then the value matches `YYYY-MM-DDTHH:MM:SSZ` (UTC, suffix `Z`). | all datetime EPs / — |
| REQ-208 | cross | system | IDs in payloads are prefixed strings. | Given any payload field representing a resource identifier, when serialized, then the value is a prefixed string per §13 (`CUST-…`, `ACC-…`, `LINE-…`, `SIM-…`, `PUR-…`, `PROMO-…`, `TCK-…`, `DATA-…GB-…D`) and never an integer. | all EPs / all entities |
| REQ-209 | cross | system | Audit events written for material actions. | Given a successful login, purchase, plan change, refund request, or ticket creation, when the request completes, then an `AuditEvent` row exists with `eventType` matching the action (`LOGIN_SUCCESS`, `PURCHASE_COMPLETED`, `PLAN_CHANGE`, `REFUND_REQUESTED`, `SUPPORT_TICKET_CREATED`), `actorId` = customer ID, and a timestamp. Audit failure does not fail the parent request. | login/purchase/plan/refund/ticket EPs / AuditEvent |
| REQ-210 | cross | system | Customers can update their contact details. | Given a valid bearer token and a partial `{email, address, notificationPreferences}` payload, when `PUT /api/customers/me/contact-details` is called, then the response is `200` with the updated profile and only the supplied fields are modified. | `PUT /api/customers/me/contact-details` / Customer |
| REQ-211 | cross | system | Customers can list their mobile lines and SIM profile. | Given a valid bearer token, when `GET /api/customers/me/lines` and `GET /api/customers/me/sim-profile` are called, then both return `200` with the §11-shaped payloads. | `GET /api/customers/me/lines`, `GET /api/customers/me/sim-profile` / MobileLine, SIMProfile |
| REQ-212 | cross | system | Customers can list and update notification preferences. | Given a valid bearer token, when `GET /api/notifications` is called, then the response is a cursor-paginated list of past notifications. When `POST /api/notifications/preferences` is called with `{push, sms, email, inApp}`, then preferences are persisted and reflected in subsequent `GET`s. | `GET /api/notifications`, `POST /api/notifications/preferences` / Notification, Customer |

## Open questions

- **OTP enrollment surface.** §13.1 says OTP is per-customer but does not specify how a customer becomes OTP-enrolled. Phase 1 will treat OTP enrollment as a seeded property of the `Customer` row (no enrollment endpoint). Stage 02 should confirm.
- **Refund settlement timing.** §13.2 says refunds are async. REQ-084 commits only to ticket creation; the actual settlement workflow is deferred. Stage 02 should decide whether `GET /api/accounts/me/refunds/{refundId}` is part of phase 1.
- **Invoice line items.** §11 names `Invoice` but does not enumerate line items. REQ-081 introduces a line-item array; stage 03 must decide whether this is a separate `InvoiceLineItem` entity or denormalized JSON.
- **Provisioning observability.** §9.2 step 9 says "the provisioning system activates the bundle". Phase 1 simulates this by logging an audit event. Stage 02 should decide whether the customer can see the provisioning status (e.g. on the purchase detail).
- **Attachment storage.** REQ-104 caps attachments at 10 MB but does not specify storage. Stage 03 should decide between filesystem under `output/backend/uploads/` (phase 1 default) or DB BLOB.
- **Notification delivery.** REQ-012 stubs push delivery. Stage 02 should make explicit that `POST /api/notifications/device-token` returns `204` and does not call FCM.
- **Customer support agent identity.** §9.6 step 5 says "a support agent reviews the ticket" but phase 1 has no agent role implementation. Tickets default to unassigned; reply-from-agent is out of phase 1.

## OUT-OF-PHASE-1

- **Administration portal (§7.13)** — no admin endpoints, no `Admin*` routes. Internal balance adjustments, customer search, audit-log viewer are deferred.
- **Real payment gateway** — top-ups and refunds simulate. No 3DS, no card storage, no Stripe/Adyen integration.
- **Real provisioning system** — purchases write an audit event; no call to a provisioning system.
- **Real FCM / push delivery** — device tokens are stored but `Notification` rows are not pushed.
- **Customer-support-agent inbound replies on tickets** — `TicketMessage.author` is always the customer in phase 1.
- **Refund dispute manual workflow (§13.2)** — `POST /api/accounts/me/refunds` creates a pending row; the resolution workflow is deferred.
- **Internationalization** — strings English-only; locale plumbing OK but no translations.
- **Rate limiting / WAF** — document the seam in stage 04, do not enforce.
- **Loyalty platform integration (§7.15)** — `loyaltyTier` is read from the seeded customer row; no points engine.
- **Campaign management automation** — promotions are seeded; no campaign CRUD endpoint.
