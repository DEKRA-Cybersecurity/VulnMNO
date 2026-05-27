# Screen template

## Shape of a `SCR-` entry

```
### SCR-004 ShopScreen

- **Journey:** §9.2 Purchase of a data bundle
- **Route:** `shop`
- **Reads (on entry / refresh):**
  - `EP-020 GET /api/shop/products` → `List<ProductRead>`
- **Writes (on user action):**
  - User taps a product → navigate to `SCR-005 ProductDetailScreen` (no API call)
- **UiState:**
  - `Loading`
  - `Content(products: List<Product>, filter: Category?)`
  - `Error(message: String, retryable: Boolean)`
- **Navigation in:**
  - From `SCR-001 HomeScreen` bottom-nav tap → `NAV-010`
  - From deep link `vulnmno://shop`
- **Navigation out:**
  - `SCR-005 ProductDetailScreen(productId)` on item tap → `NAV-011`
  - `SCR-001 HomeScreen` on bottom-nav home tap
- **Auth requirement:** Requires authenticated session. `401` → drop tokens → `SCR-000 LoginScreen` (deep link to `shop` preserved).
- **Empty state:** "No products available." with a Retry button bound to the same `EP-020` call.
- **Error states:**
  - Network error → retryable error UI.
  - `RATE_LIMITED` → non-retryable error with cooldown message.
- **Notes:** Filter chips are client-side only in phase 1.
```

## Required fields per `SCR-`

- Journey, Route, Reads, Writes, UiState, Navigation in, Navigation out, Auth requirement, Empty state, Error states.

Optional: Notes, Telemetry (out of phase 1 scope; document the seam if anything will be measured).

## State model rules

- Every screen's `UiState` is a sealed interface with at minimum `Loading`, `Content(...)`, `Error(...)`.
- Transient sub-states (`OtpChallenge`, `Submitting`, `Confirmed`) are added only when the screen genuinely cannot be represented in `Content`. Avoid `isLoading: Boolean` flags on `Content`.
- ViewModels expose `StateFlow<UiState>`. They never expose mutable state or raw network types.

## Navigation rules

- One Compose `NavHost` lives in `MainActivity`. Bottom-nav top-level destinations: Home, Shop, Plans, Usage, Support.
- Account, Balance, Invoices and Notifications are reachable from Home and from a drawer/profile menu, but they are not bottom-nav items.
- OTP screen has no back action that returns to `LoginScreen` with the password preserved — going back drops the challenge and starts login fresh.
- After a successful purchase, back from `PurchaseConfirmationScreen` returns to `ShopScreen`, not `CheckoutScreen`. Document this as a `NAV-…` rule.
- `401` from any API call dispatches a global navigation event that pops the back-stack to `LoginScreen` and preserves the user's intended deep link for post-login redirect.

## Empty / error / offline policy

- **Empty:** Always render a textual empty state with one primary action (Retry, Browse, Create). Never an empty screen.
- **Error:** Distinguish retryable (network, 5xx) from non-retryable (400, 409). Retryable shows a Retry button; non-retryable shows the message and a navigation alternative.
- **Offline:** Out of phase 1 scope as a first-class feature, but the app should detect offline (`ConnectivityManager`) and surface it as a retryable error rather than a generic failure.
