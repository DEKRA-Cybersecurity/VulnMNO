# UI state model — phase 1

## Scope

Per-screen `UiState` definitions. Each state is a Kotlin sealed interface; stage 06 translates these verbatim into Kotlin. Every state has at minimum `Loading`, `Content(...)`, `Error(...)`; transient sub-states (`Submitting`, `OtpChallenge`, etc.) are only added where genuinely needed.

## Inputs consumed

- [screens.md](screens.md) — `SCR-…` entries and per-screen reads/writes.
- `_config/code-style.md` — `UiState` convention.
- `02_api_contract/output/error-codes.md` — surfaced via `AppError.code` mapping.

## Conventions

Throughout this document:

```kotlin
sealed interface UiState
data object Loading : UiState
data class  Error(val message: String, val retryable: Boolean) : UiState
```

`Error.retryable` distinguishes 5xx / network (`true`) from 4xx domain (`false`). Domain errors with a `details.rule` are exposed via field-level error state inside `Content(...)` rather than a screen-level error.

Domain models referenced below (`Customer`, `Product`, `Promotion`, `Plan`, `PlanChange`, `Purchase`, `Balance`, `Transaction`, `UsageRecord`, `Ticket`, `TicketMessage`, `TicketAttachment`, `Notification`, `Invoice`, `InvoiceLineItem`) live in `domain/model/`. They are NOT the wire DTOs; mapping happens in repositories.

## Per-screen UI states

### SCR-001 SplashScreen

```kotlin
sealed interface SplashUiState {
    data object Resolving : SplashUiState
    data class  LoggedIn(val customerId: String) : SplashUiState
    data object LoggedOut : SplashUiState
}
```

### SCR-002 LoginScreen

```kotlin
data class LoginUiState(
    val msisdn: String = "",
    val password: String = "",
    val submitting: Boolean = false,
    val msisdnError: String? = null,
    val passwordError: String? = null,
    val formError: String? = null,
)
```

Mappings:
- `INVALID_CREDENTIALS` → `formError = "Phone number or password incorrect"`.
- Network → snackbar via a side-channel `Event<String>` exposed by the ViewModel.

### SCR-003 OtpScreen

```kotlin
data class OtpUiState(
    val challengeToken: String,
    val code: String = "",
    val attemptsLeft: Int = 5,
    val submitting: Boolean = false,
    val codeError: String? = null,
    val resendCooldownSeconds: Int = 0,
)
```

### SCR-004 PasswordResetRequestScreen

```kotlin
data class PwResetRequestUiState(
    val msisdn: String = "",
    val submitting: Boolean = false,
    val success: Boolean = false,
)
```

### SCR-005 PasswordResetConfirmScreen

```kotlin
data class PwResetConfirmUiState(
    val msisdn: String,
    val code: String = "",
    val newPassword: String = "",
    val submitting: Boolean = false,
    val codeError: String? = null,
    val passwordError: String? = null,
)
```

### SCR-006 HomeScreen

```kotlin
data class HomeUiState(
    val profile: Section<Customer> = Section.Loading,
    val balance: Section<Balance> = Section.Loading,
    val currentPlan: Section<Plan> = Section.Loading,
    val featuredOffers: Section<List<Product>> = Section.Loading,
)

sealed interface Section<out T> {
    data object Loading : Section<Nothing>
    data class  Loaded<T>(val value: T) : Section<T>
    data class  Failed(val retryable: Boolean) : Section<Nothing>
}
```

The four sections render independently. A partial dashboard is still useful.

### SCR-007 AccountScreen

```kotlin
sealed interface AccountUiState {
    data object Loading : AccountUiState
    data class  Content(
        val customer: Customer,
        val lines: List<MobileLine>,
        val draft: ContactDetailsDraft,
        val savingState: SavingState = SavingState.Idle,
    ) : AccountUiState
    data class  Error(val message: String, val retryable: Boolean) : AccountUiState
}

data class ContactDetailsDraft(
    val email: String?,
    val billingAddress: Address?,
    val prefs: NotificationPreferencesDraft,
)

sealed interface SavingState {
    data object Idle : SavingState
    data object Saving : SavingState
    data class  FieldErrors(val fields: Map<String, String>) : SavingState
}
```

### SCR-008 SimProfileScreen

```kotlin
sealed interface SimUiState {
    data object Loading : SimUiState
    data class  Content(val sim: SimProfile) : SimUiState
    data class  Error(val message: String, val retryable: Boolean) : SimUiState
}
```

### SCR-009 BalanceScreen

```kotlin
sealed interface BalanceUiState {
    data object Loading : BalanceUiState
    data class  Content(val balance: Balance, val lastTopUp: Transaction?) : BalanceUiState
    data class  Error(val message: String, val retryable: Boolean) : BalanceUiState
}
```

### SCR-010 TopUpScreen

```kotlin
data class TopUpUiState(
    val amount: BigDecimal = BigDecimal("10.00"),
    val idempotencyKey: String,                       // generated in SavedStateHandle
    val submitting: Boolean = false,
    val amountError: String? = null,
    val resultBalance: BigDecimal? = null,            // non-null → snackbar + nav back
)
```

### SCR-011 TransactionsScreen

```kotlin
data class TransactionsUiState(val paging: PagingState<Transaction>)

sealed interface PagingState<out T> {
    data object Loading : PagingState<Nothing>
    data class  Content<T>(val items: List<T>) : PagingState<T>          // emitted continuously by paging-3
    data class  Error(val retryable: Boolean) : PagingState<Nothing>
}
```

`PagingState` is reused by every paginated list screen below.

### SCR-012 ShopScreen

```kotlin
data class ShopUiState(
    val paging: PagingState<Product>,
    val category: ProductCategory? = null,
)
```

### SCR-013 ProductDetailScreen

```kotlin
sealed interface ProductDetailUiState {
    data object Loading : ProductDetailUiState
    data class  Content(val product: Product) : ProductDetailUiState
    data class  Error(val message: String, val retryable: Boolean) : ProductDetailUiState
}
```

### SCR-014 CheckoutScreen

```kotlin
sealed interface CheckoutUiState {
    data object Loading : CheckoutUiState
    data class  Content(
        val product: Product,
        val balance: Balance,
        val promoCode: String = "",
        val promo: PromoStatus = PromoStatus.NotApplied,
        val purchasing: Boolean = false,
        val purchaseError: PurchaseError? = null,
        val idempotencyKey: String,
    ) : CheckoutUiState
    data class  Error(val message: String, val retryable: Boolean) : CheckoutUiState
}

sealed interface PromoStatus {
    data object NotApplied : PromoStatus
    data object Applying : PromoStatus
    data class  Applied(val promo: PromoApplication) : PromoStatus
    data class  Invalid(val message: String) : PromoStatus       // PROMO_INVALID
    data class  Ineligible(val rule: String) : PromoStatus       // PROMO_INELIGIBLE
}

sealed interface PurchaseError {
    data class InsufficientBalance(val shortfall: BigDecimal) : PurchaseError
    data class IdempotencyConflict(val message: String) : PurchaseError
    data class Generic(val message: String) : PurchaseError
}
```

### SCR-015 PurchaseConfirmationScreen

```kotlin
data class PurchaseConfirmationUiState(val purchase: Purchase)
```

No loading/error state — the screen receives the purchase as a nav-arg from `SCR-014`.

### SCR-016 PlansScreen

```kotlin
sealed interface PlansUiState {
    data object Loading : PlansUiState
    data class  Content(
        val current: Plan,
        val available: List<Plan>,
        val pending: PendingPlanChange? = null,           // surfaced as a top banner
    ) : PlansUiState
    data class  Error(val message: String, val retryable: Boolean) : PlansUiState
}
```

### SCR-017 PlanChangeScreen

```kotlin
sealed interface PlanChangeUiState {
    data object Loading : PlanChangeUiState
    data class  Content(
        val current: Plan,
        val target: Plan,
        val mode: PlanChangeMode = PlanChangeMode.Immediate,
        val effectiveDate: LocalDate? = null,
        val submitting: Boolean = false,
        val ineligibleRule: String? = null,
        val pendingBlock: PendingPlanChange? = null,
    ) : PlanChangeUiState
    data class  Error(val message: String, val retryable: Boolean) : PlanChangeUiState
}

enum class PlanChangeMode { Immediate, Scheduled }
```

### SCR-018 UsageScreen

```kotlin
enum class UsageTab { Calls, Sms, Data, Roaming }

data class UsageUiState(
    val tab: UsageTab = UsageTab.Calls,
    val dateRange: DateRange = DateRange.last30Days(),
    val paging: PagingState<UsageRecord>,
    val exporting: Boolean = false,
)
```

### SCR-019 InvoicesScreen

```kotlin
data class InvoicesUiState(val paging: PagingState<InvoiceSummary>)
```

### SCR-020 InvoiceDetailScreen

```kotlin
sealed interface InvoiceDetailUiState {
    data object Loading : InvoiceDetailUiState
    data class  Content(val invoice: Invoice, val downloading: Boolean = false) : InvoiceDetailUiState
    data class  Error(val message: String, val retryable: Boolean) : InvoiceDetailUiState
}
```

### SCR-021 RefundRequestScreen

```kotlin
data class RefundRequestUiState(
    val targetType: RefundTarget,
    val targetId: String,
    val reason: String = "",
    val submitting: Boolean = false,
    val reasonError: String? = null,
)

enum class RefundTarget { Purchase, Invoice }
```

### SCR-022 SupportTicketsScreen

```kotlin
data class SupportTicketsUiState(
    val paging: PagingState<TicketSummary>,
    val statusFilter: TicketStatus? = null,
)
```

### SCR-023 NewTicketScreen

```kotlin
data class NewTicketUiState(
    val topic: TicketTopic = TicketTopic.Other,
    val description: String = "",
    val submitting: Boolean = false,
    val descriptionError: String? = null,
)
```

### SCR-024 TicketDetailScreen

```kotlin
sealed interface TicketDetailUiState {
    data object Loading : TicketDetailUiState
    data class  Content(
        val ticket: Ticket,
        val draftReply: String = "",
        val sending: Boolean = false,
        val attaching: Boolean = false,
        val closed: Boolean = ticket.status == TicketStatus.Closed,
    ) : TicketDetailUiState
    data class  Error(val message: String, val retryable: Boolean) : TicketDetailUiState
}
```

`TICKET_CLOSED` from `EP-063` / `EP-064` flips `closed = true` and disables the input. The screen does not navigate away.

### SCR-025 NotificationsScreen

```kotlin
sealed interface NotificationsUiState {
    data object Loading : NotificationsUiState
    data class  Content(
        val paging: PagingState<Notification>,
        val preferences: NotificationPreferences,
        val updatingPrefs: Boolean = false,
    ) : NotificationsUiState
    data class  Error(val message: String, val retryable: Boolean) : NotificationsUiState
}
```

## Cross-cutting concerns

### Error → UiState mapping

| `error.code` | Surfacing |
| --- | --- |
| `UNAUTHENTICATED`, `TOKEN_EXPIRED`, `TOKEN_REVOKED` | Caught by the global `AuthListener`; triggers NAV-034 (drop to `LoginScreen`). Screen `UiState` never sees these. |
| `VALIDATION_FAILED` | Field-level errors derived from `details.errors[]`. Each ViewModel maps to the screen's `*Error` fields. |
| `RATE_LIMITED` | Snackbar with `details.retryAfterSeconds`. Non-retryable in current view. |
| `NOT_FOUND` | Screen-level `Error("Resource not found", retryable = false)`. |
| `CONFLICT` | Context-dependent; see specific screen states (e.g. `PurchaseError`, `PendingPlanChange` banner). |
| `PROMO_INVALID` / `PROMO_INELIGIBLE` | `CheckoutUiState.promo = Invalid(...) | Ineligible(...)`. |
| `INSUFFICIENT_BALANCE` | `CheckoutUiState.purchaseError = InsufficientBalance(shortfall)`. |
| `PLAN_INELIGIBLE` | `PlanChangeUiState.ineligibleRule = details.rule`. |
| `PLAN_CHANGE_PENDING` | `PlanChangeUiState.pendingBlock = details.pendingChange`. |
| `TICKET_CLOSED` | `TicketDetailUiState.Content.closed = true`. |
| `IDEMPOTENCY_CONFLICT` | Surfaced as `Generic(message)` on the screen that initiated the request; the original response is replayed by the server, so this rarely reaches the user. |
| `INTERNAL` | Screen-level `Error(message, retryable = true)`. |

### Side-channel events

ViewModels expose `Flow<UiEvent>` next to `StateFlow<UiState>` for one-shot effects (snackbars, navigation commands). `UiEvent` is a sealed interface per screen with cases like `NavigateBack`, `ShowSnackbar(text)`, `OpenExternal(uri)`. The Composable collects events with `LaunchedEffect`.

### Process death

All `*UiState` data classes are `Parcelable` via `@Parcelize` and stored in `SavedStateHandle`. Idempotency keys, promo codes, draft text, and pagination cursors all survive process death.
