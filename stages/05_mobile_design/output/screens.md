# Mobile screens — phase 1

## Scope

Screen inventory for the VulnMNO Android app covering journeys §9.1–§9.6. One `SCR-…` per reserved name from `shared/glossary.md`. Each entry names the endpoints it reads on entry and the endpoints it writes on user action. State definitions are in [state-model.md](state-model.md); navigation transitions in [navigation.md](navigation.md).

## Inputs consumed

- `01_requirements/output/backlog.md`
- `02_api_contract/output/openapi.yaml`
- `02_api_contract/output/endpoints.md`
- `shared/glossary.md` — reserved screen names
- `_config/conventions.md` — `SCR-` / `NAV-` shape

## Index table

| ID | Name | Journey (§9.x) | Reads (EP-) | Writes (EP-) | State (see state-model.md) | Auth |
| --- | --- | --- | --- | --- | --- | --- |
| SCR-001 | SplashScreen | bootstrap | — | — | `Resolving` → `LoggedIn` / `LoggedOut` | none |
| SCR-002 | LoginScreen | §9.1 | — | EP-001 | `LoginUiState` | none |
| SCR-003 | OtpScreen | §9.1 | — | EP-004 | `OtpUiState` | none (carries challenge token) |
| SCR-004 | PasswordResetRequestScreen | §9.1 | — | EP-005 | `PwResetRequestUiState` | none |
| SCR-005 | PasswordResetConfirmScreen | §9.1 | — | EP-006 | `PwResetConfirmUiState` | none |
| SCR-006 | HomeScreen | §9.1 | EP-010, EP-020, EP-040, EP-030 (`?featured=true`) | EP-002 (logout from menu), EP-072 (device-token on first launch) | `HomeUiState` (aggregated) | required |
| SCR-007 | AccountScreen | §9.1 | EP-010, EP-012 | EP-011 | `AccountUiState` | required |
| SCR-008 | SimProfileScreen | §9.1 | EP-013 | — | `SimUiState` | required |
| SCR-009 | BalanceScreen | §9.2, §9.5 | EP-020 | — | `BalanceUiState` | required |
| SCR-010 | TopUpScreen | §9.2 | — | EP-022 (with `Idempotency-Key`) | `TopUpUiState` | required |
| SCR-011 | TransactionsScreen | §9.5 | EP-021 (paginated) | — | `TransactionsUiState` | required |
| SCR-012 | ShopScreen | §9.2 | EP-030 (paginated, filter) | — | `ShopUiState` | required |
| SCR-013 | ProductDetailScreen | §9.2 | EP-031 | — | `ProductDetailUiState` | required |
| SCR-014 | CheckoutScreen | §9.2 | EP-031, EP-020 (refresh balance), EP-032 (on promo apply) | EP-033 (with `Idempotency-Key`) | `CheckoutUiState` | required |
| SCR-015 | PurchaseConfirmationScreen | §9.2 | — (data passed in nav arg) | — | `PurchaseConfirmationUiState` | required |
| SCR-016 | PlansScreen | §9.3 | EP-040, EP-041 | — | `PlansUiState` | required |
| SCR-017 | PlanChangeScreen | §9.3 | EP-040, EP-041 | EP-042 (with `Idempotency-Key`), EP-043 (cancel pending) | `PlanChangeUiState` | required |
| SCR-018 | UsageScreen | §9.4 | EP-050, EP-051, EP-052, EP-053 (one per tab) | EP-054 (export) | `UsageUiState(tab, dateRange)` | required |
| SCR-019 | InvoicesScreen | §9.5 | EP-023 (paginated) | — | `InvoicesUiState` | required |
| SCR-020 | InvoiceDetailScreen | §9.5 | EP-024 | EP-025 (PDF download via `Intent.ACTION_VIEW`) | `InvoiceDetailUiState` | required |
| SCR-021 | RefundRequestScreen | §9.5 | — | EP-026 | `RefundRequestUiState` | required |
| SCR-022 | SupportTicketsScreen | §9.6 | EP-061 (paginated, filter by status) | — | `SupportTicketsUiState` | required |
| SCR-023 | NewTicketScreen | §9.6 | — | EP-060 | `NewTicketUiState` | required |
| SCR-024 | TicketDetailScreen | §9.6 | EP-062 | EP-063 (message), EP-064 (attachment), EP-065 (close) | `TicketDetailUiState` | required |
| SCR-025 | NotificationsScreen | cross | EP-070 (paginated) | EP-071 (preferences inline) | `NotificationsUiState` | required |

Total: **25 screens**. Bottom-navigation top-level destinations: Home, Shop, Plans, Usage, Support. Account, Balance, Invoices, Notifications, Refund and SimProfile are reachable from the Home overflow menu and from contextual entry points (e.g. an Invoice card on Home links to InvoicesScreen).

## Per-screen entries

### SCR-001 SplashScreen

- **Journey:** bootstrap
- **Route:** `splash`
- **Reads (on entry):** reads DataStore for stored refresh token; if present, calls `EP-003 POST /api/auth/refresh` to obtain a fresh access token.
- **Writes:** none.
- **UiState:** `Resolving` → `LoggedIn(customerId)` → navigate `SCR-006 HomeScreen` | `LoggedOut` → navigate `SCR-002 LoginScreen`.
- **Navigation in:** app cold start, deep link entry.
- **Navigation out:** `SCR-002` or `SCR-006` (replaces back-stack root).
- **Empty / error / offline:** on refresh failure, drop tokens and navigate to `SCR-002`. Offline → show retry once.

### SCR-002 LoginScreen

- **Journey:** §9.1
- **Route:** `login`
- **Reads:** none.
- **Writes:** `EP-001 POST /api/auth/login` on Sign-in tap.
- **UiState:** `LoginUiState`.
- **Navigation in:** from `SCR-001`, from any screen on a `401` event (after token drop). The intended deep-link `pendingRoute` is preserved in saved state across this drop.
- **Navigation out:**
  - On `TokenPair` response → store tokens, navigate to `pendingRoute` or `SCR-006 HomeScreen`.
  - On `OtpChallenge` response → navigate to `SCR-003 OtpScreen(challengeToken)`.
  - "Forgot password?" → `SCR-004 PasswordResetRequestScreen`.
- **Auth requirement:** none.
- **Empty / error / offline:**
  - `INVALID_CREDENTIALS` → non-retryable form error under the password field.
  - Network → retryable banner.
- **Notes:** never auto-fills the password. The MSISDN field is pre-filled from `last_msisdn` in DataStore if present.

### SCR-003 OtpScreen

- **Journey:** §9.1
- **Route:** `otp`
- **Reads:** none.
- **Writes:** `EP-004 POST /api/auth/otp/verify` on Continue tap.
- **UiState:** `OtpUiState`.
- **Navigation in:** from `SCR-002` when login returned a challenge.
- **Navigation out:**
  - On `TokenPair` response → `pendingRoute` or `SCR-006`.
  - Back gesture → drops the challenge and returns to `SCR-002` with empty form.
  - Resend code → re-runs `EP-001` with the cached msisdn+password (kept in memory only for this navigation hop).
- **Empty / error / offline:**
  - `OTP_INVALID` → in-field error; allow up to 5 attempts before challenge invalidates.
  - Expired challenge → toast + back to `SCR-002`.

### SCR-004 PasswordResetRequestScreen

- **Journey:** §9.1
- **Route:** `password-reset/request`
- **Reads:** none.
- **Writes:** `EP-005 POST /api/auth/password-reset/request`.
- **UiState:** `PwResetRequestUiState`.
- **Navigation in:** from `SCR-002` "Forgot password?".
- **Navigation out:** on success → `SCR-005 PasswordResetConfirmScreen(msisdn)`. Cancel → `SCR-002`.
- **Empty / error / offline:** always shows success message regardless of whether MSISDN exists (no existence leak — REQ-203 mirror on client UX).

### SCR-005 PasswordResetConfirmScreen

- **Journey:** §9.1
- **Route:** `password-reset/confirm?msisdn={msisdn}`
- **Writes:** `EP-006 POST /api/auth/password-reset/confirm`.
- **UiState:** `PwResetConfirmUiState`.
- **Navigation in:** from `SCR-004`.
- **Navigation out:** on success → `SCR-002 LoginScreen` with the MSISDN prefilled. `OTP_INVALID` → form error.

### SCR-006 HomeScreen

- **Journey:** §9.1 (REQ-011 aggregated dashboard)
- **Route:** `home`
- **Reads (in parallel on entry / pull-to-refresh):**
  - `EP-010 GET /api/customers/me`
  - `EP-020 GET /api/accounts/me/balance`
  - `EP-040 GET /api/plans/current`
  - `EP-030 GET /api/shop/products?featured=true&limit=5`
- **Writes:**
  - `EP-072 POST /api/notifications/device-token` on first launch (token from FCM stub).
  - `EP-002 POST /api/auth/logout` from the overflow menu.
- **UiState:** `HomeUiState`. Four sub-statuses (`profile`, `balance`, `plan`, `offers`) each in `Loading | Loaded | Error`. The screen renders partial content as sections complete.
- **Navigation in:** from `SCR-001` after login, bottom-nav Home tap.
- **Navigation out:**
  - Balance card → `SCR-009 BalanceScreen` (NAV-010).
  - Plan card → `SCR-016 PlansScreen` (NAV-011).
  - Offer card → `SCR-013 ProductDetailScreen(productId)` (NAV-012).
  - Profile chip → `SCR-007 AccountScreen` (NAV-013).
  - Notifications bell → `SCR-025 NotificationsScreen` (NAV-014).
  - Overflow → Invoices, Support, Logout.
- **Empty / error / offline:** each section renders its own error tile with retry; the rest of the screen stays usable.

### SCR-007 AccountScreen

- **Journey:** §9.1
- **Route:** `account`
- **Reads:** `EP-010`, `EP-012` (paginated lines; phase-1 customers have 1 line).
- **Writes:** `EP-011 PUT /api/customers/me/contact-details` on Save.
- **UiState:** `AccountUiState`.
- **Navigation in:** Home profile chip, Home overflow.
- **Navigation out:** SimProfile card → `SCR-008`. Notification prefs edit → `SCR-025`.
- **Empty / error / offline:** Save shows a transient banner on validation/network failure; form values are preserved.

### SCR-008 SimProfileScreen

- **Journey:** §9.1
- **Route:** `sim-profile`
- **Reads:** `EP-013`.
- **Writes:** none in phase 1.
- **UiState:** `SimUiState`.
- **Navigation in:** from `SCR-007` SIM card.
- **Empty / error / offline:** standard pattern; if `NOT_FOUND` show "No SIM linked" with a contact-support CTA → `SCR-023 NewTicketScreen(topic="Technical")`.

### SCR-009 BalanceScreen

- **Journey:** §9.2, §9.5
- **Route:** `balance`
- **Reads:** `EP-020`.
- **Writes:** none. Top-up FAB → `SCR-010 TopUpScreen`. View transactions → `SCR-011`.
- **UiState:** `BalanceUiState`.

### SCR-010 TopUpScreen

- **Journey:** §9.2
- **Route:** `topup`
- **Writes:** `EP-022 POST /api/accounts/me/topup` with header `Idempotency-Key: <uuidv4>` generated per CTA tap (cached in nav-arg saved state to survive process death).
- **UiState:** `TopUpUiState`.
- **Navigation in:** from `SCR-009` FAB.
- **Navigation out:** on success → back to `SCR-009` with a snackbar showing new balance.
- **Empty / error / offline:** `IDEMPOTENCY_CONFLICT` → toast "Already processed", navigate back; `VALIDATION_FAILED` (amount out of range) → in-field error.

### SCR-011 TransactionsScreen

- **Journey:** §9.5
- **Route:** `transactions`
- **Reads:** `EP-021` (cursor pagination via LazyColumn `paging-3-compose`).
- **UiState:** `TransactionsUiState` (paged).
- **Navigation in:** from `SCR-009`. Each row tap → if `relatedPurchaseId` set, navigate `SCR-014 PurchaseDetail` (deferred — phase 1 uses `SCR-015` as detail surrogate); if `relatedInvoiceId`, → `SCR-020`.

### SCR-012 ShopScreen

- **Journey:** §9.2
- **Route:** `shop`
- **Reads:** `EP-030 GET /api/shop/products?limit=20&cursor=…&category=…`.
- **UiState:** `ShopUiState`.
- **Navigation in:** bottom-nav Shop, Home offer card → `SCR-013` (skipping `SCR-012`).
- **Navigation out:** item tap → `SCR-013 ProductDetailScreen(productId)`.
- **Empty / error / offline:** empty state "No products available" + Retry; category filter is client-side in phase 1 unless backend pagination already covers it.

### SCR-013 ProductDetailScreen

- **Journey:** §9.2
- **Route:** `product/{productId}`
- **Reads:** `EP-031`.
- **UiState:** `ProductDetailUiState`.
- **Navigation in:** from `SCR-012` row tap or `SCR-006` offer card.
- **Navigation out:** Buy → `SCR-014 CheckoutScreen(productId)`.

### SCR-014 CheckoutScreen

- **Journey:** §9.2
- **Route:** `checkout/{productId}`
- **Reads on entry:** `EP-031` (product), `EP-020` (balance) in parallel.
- **Writes on user action:**
  - Apply promo → `EP-032 POST /api/shop/promotions/apply`.
  - Confirm purchase → `EP-033 POST /api/shop/purchases` with `Idempotency-Key`.
- **UiState:** `CheckoutUiState`. Sub-status `promoStatus = NotApplied | Applying | Applied(promo) | Invalid(message) | Ineligible(rule)`.
- **Navigation in:** from `SCR-013`.
- **Navigation out:**
  - Success → `SCR-015 PurchaseConfirmationScreen(purchaseId)`.
  - `INSUFFICIENT_BALANCE` → keep on screen with an error banner + Top-up CTA → `SCR-010`.
- **Empty / error / offline:** `PROMO_INVALID` / `PROMO_INELIGIBLE` highlight the promo field with the `details.rule` text; purchase button stays disabled while promo is being applied.

### SCR-015 PurchaseConfirmationScreen

- **Journey:** §9.2
- **Route:** `purchase-confirmation/{purchaseId}`
- **Reads:** purchase payload passed as nav-arg (no extra call).
- **UiState:** `PurchaseConfirmationUiState`.
- **Navigation in:** from `SCR-014` success.
- **Navigation out:**
  - Done → pops back-stack to `SCR-012 ShopScreen` (skips `SCR-013` and `SCR-014` per NAV rule).
  - View receipt → no-op in phase 1; documented as future.
- **Empty / error / offline:** N/A — purely a confirmation surface.

### SCR-016 PlansScreen

- **Journey:** §9.3
- **Route:** `plans`
- **Reads:** `EP-040` (current) + `EP-041` (available) in parallel.
- **UiState:** `PlansUiState`.
- **Navigation in:** bottom-nav Plans, Home plan card.
- **Navigation out:** "Change plan" CTA → `SCR-017 PlanChangeScreen(planId)`.

### SCR-017 PlanChangeScreen

- **Journey:** §9.3
- **Route:** `plan-change/{planId}`
- **Reads:** `EP-040`, `EP-041` (cached from `SCR-016`).
- **Writes:** `EP-042 POST /api/plans/change` (immediate/scheduled), `EP-043 POST /api/plans/change/{changeId}/cancel` from a pending-banner.
- **UiState:** `PlanChangeUiState`.
- **Navigation in:** from `SCR-016`.
- **Navigation out:** success (immediate or scheduled) → back to `SCR-016` with snackbar.
- **Empty / error / offline:** `PLAN_INELIGIBLE` → render the `details.rule` as a help-text under the plan card; `PLAN_CHANGE_PENDING` → render a banner offering "Cancel pending change" → `EP-043`.

### SCR-018 UsageScreen

- **Journey:** §9.4
- **Route:** `usage`
- **Internal tabs:** `calls | sms | data | roaming`.
- **Reads:** one of `EP-050 / EP-051 / EP-052 / EP-053` per tab, with the current date range filter.
- **Writes:** `EP-054 GET /api/usage/export?format=csv|json` from overflow menu (downloads to Downloads/ via `MediaStore`).
- **UiState:** `UsageUiState(tab, dateRange, items)`.
- **Navigation in:** bottom-nav Usage.
- **Empty / error / offline:** "No usage in this period" empty state per tab; invalid range → in-field error.

### SCR-019 InvoicesScreen

- **Journey:** §9.5
- **Route:** `invoices`
- **Reads:** `EP-023` paginated.
- **UiState:** `InvoicesUiState`.
- **Navigation in:** Home overflow, from `SCR-009`.
- **Navigation out:** row tap → `SCR-020 InvoiceDetailScreen(invoiceId)`.

### SCR-020 InvoiceDetailScreen

- **Journey:** §9.5
- **Route:** `invoice/{invoiceId}`
- **Reads:** `EP-024`.
- **Writes:** Download PDF via `EP-025` (handled outside Compose: opens with `Intent.ACTION_VIEW` using `FileProvider`).
- **UiState:** `InvoiceDetailUiState`.
- **Navigation in:** from `SCR-019`.
- **Navigation out:** "Request refund" → `SCR-021 RefundRequestScreen(targetType=invoice, targetId)`.

### SCR-021 RefundRequestScreen

- **Journey:** §9.5
- **Route:** `refund?targetType={t}&targetId={id}`
- **Writes:** `EP-026 POST /api/accounts/me/refunds`.
- **UiState:** `RefundRequestUiState`.
- **Navigation in:** from `SCR-020` (invoice) or `SCR-011` (purchase row).
- **Navigation out:** on `202` → `SCR-024 TicketDetailScreen(ticketId)` using the `ticketId` returned in the body.

### SCR-022 SupportTicketsScreen

- **Journey:** §9.6
- **Route:** `support`
- **Reads:** `EP-061` (paginated, filterable by status).
- **UiState:** `SupportTicketsUiState`.
- **Navigation in:** bottom-nav Support.
- **Navigation out:** FAB → `SCR-023 NewTicketScreen`. Row tap → `SCR-024 TicketDetailScreen(ticketId)`.

### SCR-023 NewTicketScreen

- **Journey:** §9.6
- **Route:** `support/new?topic={topic?}`
- **Writes:** `EP-060 POST /api/support/tickets`.
- **UiState:** `NewTicketUiState`.
- **Navigation in:** from `SCR-022` FAB; with `topic` arg from other screens (e.g. `SCR-008` "Contact support").
- **Navigation out:** success → `SCR-024 TicketDetailScreen(ticketId)`.

### SCR-024 TicketDetailScreen

- **Journey:** §9.6
- **Route:** `support/ticket/{ticketId}`
- **Reads:** `EP-062`.
- **Writes:** `EP-063` (message), `EP-064` (attachment), `EP-065` (close).
- **UiState:** `TicketDetailUiState`.
- **Navigation in:** from `SCR-022`, `SCR-023`, or `SCR-021`.
- **Empty / error / offline:** `TICKET_CLOSED` on message/attachment → disable input, render closed banner. Attachment > 10 MB → in-field error before upload.

### SCR-025 NotificationsScreen

- **Journey:** cross-cutting
- **Route:** `notifications`
- **Reads:** `EP-070` paginated.
- **Writes:** `EP-071 POST /api/notifications/preferences` from the overflow menu (modal sheet with 4 toggles: push/sms/email/inApp).
- **UiState:** `NotificationsUiState`.
- **Navigation in:** Home bell, Account screen "Notification preferences".

## Open questions

- **Pagination strategy.** All paged screens use cursor pagination via Paging 3. We assume `androidx.paging:paging-compose 3.3+`. Stage 06 confirms the dependency.
- **Idempotency keys.** Generated as UUIDv4 on the screen, persisted in `SavedStateHandle` for the duration of the screen, dropped on success. Stage 06 implements the convention in a `IdempotentRequest` helper.
- **PDF rendering.** Phase 1 opens the PDF in an external viewer via `Intent.ACTION_VIEW` and a `FileProvider`. In-app rendering is out of scope.
- **Push delivery.** Not in phase 1. `SCR-006` registers the device token (`EP-072`); no message handler is wired beyond storage.
