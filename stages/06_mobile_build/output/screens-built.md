# Screens built — stage 06

Mapping of every `SCR-…` from [stages/05_mobile_design/output/screens.md](../../05_mobile_design/output/screens.md) to the Kotlin file(s) implementing it.

| SCR | Name | File | ViewModel | Status |
| --- | --- | --- | --- | --- |
| SCR-001 | SplashScreen | [auth/AuthScreens.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/auth/AuthScreens.kt) | — (drives via `AuthGate`) | ✅ |
| SCR-002 | LoginScreen | auth/AuthScreens.kt | `LoginViewModel` | ✅ |
| SCR-003 | OtpScreen | auth/AuthScreens.kt | `OtpViewModel` | ✅ |
| SCR-004 | PasswordResetRequestScreen | auth/AuthScreens.kt | `PwResetViewModel` | ✅ |
| SCR-005 | PasswordResetConfirmScreen | auth/AuthScreens.kt | `PwResetViewModel` | ✅ |
| SCR-006 | HomeScreen | [home/HomeScreen.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/home/HomeScreen.kt) | `HomeViewModel` (4 parallel reads) | ✅ |
| SCR-007 | AccountScreen | [account/AccountScreens.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/account/AccountScreens.kt) | `AccountViewModel` | ✅ |
| SCR-008 | SimProfileScreen | account/AccountScreens.kt | `SimViewModel` | ✅ |
| SCR-009 | BalanceScreen | [balance/BalanceScreens.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/balance/BalanceScreens.kt) | `BalanceViewModel` | ✅ |
| SCR-010 | TopUpScreen | balance/BalanceScreens.kt | `TopUpViewModel` (uuid `Idempotency-Key`) | ✅ |
| SCR-011 | TransactionsScreen | balance/BalanceScreens.kt | `TransactionsViewModel` | ✅ |
| SCR-012 | ShopScreen | [shop/ShopScreens.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/shop/ShopScreens.kt) | `ShopViewModel` | ✅ |
| SCR-013 | ProductDetailScreen | shop/ShopScreens.kt | `ProductDetailViewModel` | ✅ |
| SCR-014 | CheckoutScreen | shop/ShopScreens.kt | `CheckoutViewModel` (promo Apply/Invalid/Ineligible/Applied + Idempotency-Key) | ✅ |
| SCR-015 | PurchaseConfirmationScreen | shop/ShopScreens.kt | — (nav arg only) | ✅ |
| SCR-016 | PlansScreen | [plans/PlansScreens.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/plans/PlansScreens.kt) | `PlansViewModel` | ✅ |
| SCR-017 | PlanChangeScreen | plans/PlansScreens.kt | `PlanChangeViewModel` (PLAN_INELIGIBLE rule surfaced) | ✅ |
| SCR-018 | UsageScreen | [usage/UsageScreen.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/usage/UsageScreen.kt) | `UsageViewModel` (4 tabs) | ✅ |
| SCR-019 | InvoicesScreen | [invoices/InvoicesScreens.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/invoices/InvoicesScreens.kt) | `InvoicesViewModel` | ✅ |
| SCR-020 | InvoiceDetailScreen | invoices/InvoicesScreens.kt | `InvoiceDetailViewModel` | ✅ |
| SCR-021 | RefundRequestScreen | invoices/InvoicesScreens.kt | `RefundViewModel` (nav to ticket on 202) | ✅ |
| SCR-022 | SupportTicketsScreen | [support/SupportScreens.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/support/SupportScreens.kt) | `SupportListViewModel` | ✅ |
| SCR-023 | NewTicketScreen | support/SupportScreens.kt | `NewTicketViewModel` | ✅ |
| SCR-024 | TicketDetailScreen | support/SupportScreens.kt | `TicketDetailViewModel` (TICKET_CLOSED branch) | ✅ |
| SCR-025 | NotificationsScreen | account/AccountScreens.kt | `NotificationsViewModel` | ✅ |

**25/25 screens scaffolded.**

## Cross-cutting infrastructure

| Concern | Where |
| --- | --- |
| App entrypoint + Hilt | [VulnMnoApp.kt](android/app/src/main/java/com/vulnmno/app/VulnMnoApp.kt), [MainActivity.kt](android/app/src/main/java/com/vulnmno/app/MainActivity.kt) |
| Theme | [ui/theme/Theme.kt](android/app/src/main/java/com/vulnmno/app/ui/theme/Theme.kt) (Material 3, dynamic colors) |
| DTOs (one file, ~60 schemas) | [data/remote/dto/Dtos.kt](android/app/src/main/java/com/vulnmno/app/data/remote/dto/Dtos.kt) |
| ApiService (42 endpoints) | [data/remote/ApiService.kt](android/app/src/main/java/com/vulnmno/app/data/remote/ApiService.kt) |
| Token storage | [data/local/TokenStore.kt](android/app/src/main/java/com/vulnmno/app/data/local/TokenStore.kt) (DataStore Preferences) |
| `Authorization` header + 401 refresh | [data/remote/AuthInterceptor.kt](android/app/src/main/java/com/vulnmno/app/data/remote/AuthInterceptor.kt), [data/remote/TokenAuthenticator.kt](android/app/src/main/java/com/vulnmno/app/data/remote/TokenAuthenticator.kt) |
| AppError mapping (HttpException → Domain/Network/Unknown) | [data/remote/ApiResult.kt](android/app/src/main/java/com/vulnmno/app/data/remote/ApiResult.kt) |
| Hilt graph | [di/NetworkModule.kt](android/app/src/main/java/com/vulnmno/app/di/NetworkModule.kt) |
| Repositories (one per resource group) | [data/repository/Repositories.kt](android/app/src/main/java/com/vulnmno/app/data/repository/Repositories.kt) |
| Auth orchestrator | [ui/navigation/AuthGate.kt](android/app/src/main/java/com/vulnmno/app/ui/navigation/AuthGate.kt) |
| Nav graph (single NavHost, bottom-nav 5 tabs, 6 deep links) | [ui/navigation/VulnMnoNavHost.kt](android/app/src/main/java/com/vulnmno/app/ui/navigation/VulnMnoNavHost.kt) |
| Common UI helpers (Loading/Error boxes, AppError → message) | [ui/screens/Common.kt](android/app/src/main/java/com/vulnmno/app/ui/screens/Common.kt) |

## Implementation notes vs stage-05 design

- **Idempotency keys** generated as `UUID.randomUUID().toString()` in `rememberSaveable`, so they survive process death for TopUp, Checkout and PlanChange flows.
- **`401` listener** implemented via `TokenAuthenticator` (OkHttp) + `AuthEventBus` (singleton SharedFlow) → `AuthGate` collects events and flips `AuthState`. `MainActivity`'s `LaunchedEffect(authState)` reacts by navigating to `Login` and popping the entire back-stack.
- **Bottom-nav** uses `popUpTo(graph.findStartDestination().id) { saveState = true }` + `restoreState = true` so each tab keeps its nested back-stack.
- **PurchaseConfirmation** back-stack rule: after a 201 from `EP-033`, `CheckoutScreen` calls `nav.navigate(purchaseConfirmation) { popUpTo(shop) }`, then "Done" calls `popBackStack(shop)`. Result: back from confirmation does not return to Checkout or ProductDetail.
- **EmailStr relaxed to plain String** in `CustomerDto` — same change made in the backend (stage 04) for seed data `@example.test`.

## Known gaps / deferred to stage 07

- **Compose UI tests** — directory `androidTest/` is configured in Gradle but no tests are checked in yet. Stage 07 wires the emulator-based smoke checklist.
- **JaCoCo / Compose coverage** — not run; see [coverage-summary.md](coverage-summary.md).
- **Attachment upload** — `EP-064` is exposed in `ApiService` but `TicketDetailScreen` does not yet wire a file picker. Documented as phase-1 follow-up.
- **PDF download via Intent.ACTION_VIEW** — `AccountsRepository.downloadInvoice` returns bytes; `InvoiceDetailScreen` shows a "Download" button but file routing through `FileProvider` is a phase-1 follow-up.
- **Push delivery (FCM)** — out of phase 1 by design. Device-token registration call is implemented but no FCM service is wired.
