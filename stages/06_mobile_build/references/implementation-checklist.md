# Implementation checklist

Implement screens in this order. Each screen's DoD is "happy-path UI test green + visually reaches `Content` state in the emulator against the seeded backend".

## Order

1. **Project scaffolding** — Gradle, version catalog, Hilt setup, theme, single `MainActivity` with empty `NavHost`.
2. **Networking foundation** — Retrofit + Kotlinx Serialization, `AuthInterceptor`, `TokenAuthenticator`, `DataStore`-backed token storage, error envelope mapping.
3. **LoginScreen + OtpScreen** (`SCR-000`, `SCR-001`) — establishes the auth flow used by every other screen. Test against seeded `CUST-10001`.
4. **HomeScreen** (`SCR-002`) — first authenticated screen. Reads profile, balance, current plan and promotions in parallel.
5. **AccountScreen + SimProfileScreen** — read-only customer detail.
6. **BalanceScreen + TopUpScreen + TransactionsScreen** — adds first authenticated POST flow (top-up).
7. **ShopScreen + ProductDetailScreen + CheckoutScreen + PurchaseConfirmationScreen** — the §9.2 journey end-to-end including promo application.
8. **PlansScreen + PlanChangeScreen** — §9.3.
9. **UsageScreen** (with internal tabs) — §9.4.
10. **InvoicesScreen + InvoiceDetailScreen** — §9.5. PDF download opens in `Intent.ACTION_VIEW` for phase 1; in-app PDF rendering is out of scope.
11. **SupportTicketsScreen + NewTicketScreen + TicketDetailScreen** — §9.6.
12. **NotificationsScreen** — cross-cutting; depends on `POST /api/notifications/device-token` (stub).

## Per-screen definition of done

- [ ] ViewModel exposes `StateFlow<UiState>` matching `state-model.md`.
- [ ] Repository + use cases per `_config/code-style.md`.
- [ ] DTO ↔ domain mapping in the repository, not in the ViewModel.
- [ ] All states from `state-model.md` are renderable; preview functions exist for each.
- [ ] At least one happy-path Compose UI test.
- [ ] Manual test against the emulator + seeded backend reaches `Content` and the screen looks correct.

## Cross-cutting

- **No business logic in Composables.** They render `UiState` and emit user intents to the ViewModel.
- **No raw `HttpException` reaches the UI.** Repositories map to `Result<T, AppError>` where `AppError` is sealed (`Network`, `Domain(code, message)`, `Unknown`).
- **Auth listener.** A single Hilt-scoped class observes `401` events emitted by the `TokenAuthenticator` and posts a navigation command to drop to `LoginScreen`. The destination the user was trying to reach is saved as a `pendingRoute` and resumed after login.
- **Build variants.** `debug` uses `BASE_URL=http://10.0.2.2:8000`. `release` reads `BASE_URL` from `gradle.properties`. No hard-coded URLs.
- **Testing the OpenAPI shape.** Snapshot-deserialize the `docs/VulnMNO.md` §13 example payloads in unit tests to catch DTO drift from the spec early.

## Local run

1. Boot the backend (stage 04 README).
2. Launch a Pixel 6 API 34 emulator.
3. `./gradlew :app:installDebug` from `output/android/`.
4. Open the app; log in with seeded `CUST-10001` / seed password from `setup/questionnaire.md`.
