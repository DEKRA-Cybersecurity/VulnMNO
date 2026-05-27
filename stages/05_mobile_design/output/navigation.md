# Navigation graph — phase 1

## Scope

The single `NavHost` lives inside `MainActivity`. All routes are declared as Kotlin sealed-class objects under `ui.navigation.Route`. Deep links and back-stack behavior follow the rules at the bottom.

## Inputs consumed

- [screens.md](screens.md) — `SCR-…` entries and per-screen `Navigation in / out`.
- `02_api_contract/output/auth-model.md` — `401` listener contract.
- `_config/conventions.md` — `NAV-…` IDs.

## Route hierarchy

```
NavHost (start = "splash")
├── splash                                          (SCR-001)
├── auth/
│   ├── login                                       (SCR-002)
│   ├── otp                                         (SCR-003)
│   ├── password-reset/request                      (SCR-004)
│   └── password-reset/confirm?msisdn={msisdn}      (SCR-005)
└── main/                                           ⟵ bottom-nav scaffold
    ├── home                                        (SCR-006, bottom-nav)
    ├── shop                                        (SCR-012, bottom-nav)
    │   ├── product/{productId}                     (SCR-013)
    │   ├── checkout/{productId}                    (SCR-014)
    │   └── purchase-confirmation/{purchaseId}      (SCR-015)
    ├── plans                                       (SCR-016, bottom-nav)
    │   └── plan-change/{planId}                    (SCR-017)
    ├── usage                                       (SCR-018, bottom-nav)
    └── support                                     (SCR-022, bottom-nav)
        ├── support/new?topic={topic?}              (SCR-023)
        └── support/ticket/{ticketId}               (SCR-024)
    ─── (reachable from Home overflow / cards, not on bottom-nav)
    ├── account                                     (SCR-007)
    │   └── sim-profile                             (SCR-008)
    ├── balance                                     (SCR-009)
    │   ├── topup                                   (SCR-010)
    │   └── transactions                            (SCR-011)
    ├── invoices                                    (SCR-019)
    │   └── invoice/{invoiceId}                     (SCR-020)
    ├── refund?targetType={t}&targetId={id}         (SCR-021)
    └── notifications                               (SCR-025)
```

## Bottom-nav

Five top-level destinations, each owning an independent back-stack (`launchSingleTop = true`, `saveState = true`, `restoreState = true`):

| Tab | Start route | Icon |
| --- | --- | --- |
| Home | `home` | `Icons.Outlined.Home` |
| Shop | `shop` | `Icons.Outlined.LocalMall` |
| Plans | `plans` | `Icons.Outlined.Layers` |
| Usage | `usage` | `Icons.Outlined.QueryStats` |
| Support | `support` | `Icons.Outlined.SupportAgent` |

## NAV transitions

| ID | From | Trigger | To | Back-stack rule |
| --- | --- | --- | --- | --- |
| NAV-001 | `splash` | refresh-token present, refresh succeeds | `main/home` | `popUpTo("splash") { inclusive = true }` |
| NAV-002 | `splash` | no token / refresh fails | `auth/login` | `popUpTo("splash") { inclusive = true }` |
| NAV-003 | `auth/login` | `TokenPair` response | `main/home` or `pendingRoute` | `popUpTo("auth/login") { inclusive = true }` (clears `pendingRoute`) |
| NAV-004 | `auth/login` | `OtpChallenge` response | `auth/otp` (carries `challengeToken` in nav-arg) | preserves login back-stack |
| NAV-005 | `auth/login` | "Forgot password?" tap | `auth/password-reset/request` | normal push |
| NAV-006 | `auth/otp` | success | `main/home` or `pendingRoute` | `popUpTo("auth/login") { inclusive = true }` |
| NAV-007 | `auth/otp` | back gesture | `auth/login` (form reset, challenge dropped) | normal pop |
| NAV-008 | `auth/password-reset/request` | success | `auth/password-reset/confirm?msisdn=…` | normal push |
| NAV-009 | `auth/password-reset/confirm` | success | `auth/login` (MSISDN prefilled) | `popUpTo("auth/login")` |
| NAV-010 | `main/home` | Balance card tap | `main/balance` | normal push |
| NAV-011 | `main/home` | Plan card tap | `main/plans` | switches bottom-nav to Plans tab |
| NAV-012 | `main/home` | Offer card tap | `main/product/{productId}` | switches bottom-nav to Shop tab, pushes detail |
| NAV-013 | `main/home` | profile chip tap | `main/account` | normal push |
| NAV-014 | `main/home` | bell tap | `main/notifications` | normal push |
| NAV-015 | `main/account` | "Edit notification prefs" | `main/notifications` (prefs sheet open) | normal push |
| NAV-016 | `main/shop` | item tap | `main/product/{productId}` | normal push |
| NAV-017 | `main/product/{productId}` | Buy | `main/checkout/{productId}` | normal push |
| NAV-018 | `main/checkout/{productId}` | purchase 201 | `main/purchase-confirmation/{purchaseId}` | `popUpTo("main/shop")` (clears `product/`, `checkout/`) |
| NAV-019 | `main/purchase-confirmation/{purchaseId}` | Done | `main/shop` | `popUpTo("main/shop") { inclusive = false }` |
| NAV-020 | `main/plans` | "Change plan" CTA | `main/plan-change/{planId}` | normal push |
| NAV-021 | `main/plan-change/{planId}` | success | `main/plans` | `popUpTo("main/plans") { inclusive = false }` |
| NAV-022 | `main/invoices` | row tap | `main/invoice/{invoiceId}` | normal push |
| NAV-023 | `main/invoice/{invoiceId}` | "Request refund" | `main/refund?targetType=invoice&targetId={id}` | normal push |
| NAV-024 | `main/refund` | 202 | `main/support/ticket/{ticketId}` | `popUpTo("main/refund") { inclusive = true }` |
| NAV-025 | `main/support` | FAB | `main/support/new` | normal push |
| NAV-026 | `main/support/new` | 201 | `main/support/ticket/{ticketId}` | `popUpTo("main/support/new") { inclusive = true }` |
| NAV-027 | `main/support` | row tap | `main/support/ticket/{ticketId}` | normal push |
| NAV-028 | `main/balance` | FAB Top-up | `main/topup` | normal push |
| NAV-029 | `main/balance` | "View transactions" | `main/transactions` | normal push |
| NAV-030 | `main/transactions` | row tap (purchase-related) | `main/purchase-confirmation/{purchaseId}` | normal push |
| NAV-031 | `main/transactions` | row tap (invoice-related) | `main/invoice/{invoiceId}` | normal push |
| NAV-032 | `main/account` | SIM card tap | `main/sim-profile` | normal push |
| NAV-033 | `main/usage` | overflow Export | external file viewer (no nav) | side-effect only |
| NAV-034 | any | `401` from any request | `auth/login` (carries `pendingRoute` in `SavedStateHandle`) | `popUpTo(start) { inclusive = true }` clears entire back-stack |
| NAV-035 | any | logout (overflow menu) | `auth/login` | `popUpTo(start) { inclusive = true }` clears entire back-stack, drops tokens, calls `EP-002` |

## Deep links

| URI | Maps to | Notes |
| --- | --- | --- |
| `vulnmno://home` | `main/home` | default after login |
| `vulnmno://shop` | `main/shop` | bottom-nav switch |
| `vulnmno://product/{productId}` | `main/product/{productId}` | |
| `vulnmno://invoice/{invoiceId}` | `main/invoice/{invoiceId}` | from notification "Your invoice is ready" |
| `vulnmno://support/ticket/{ticketId}` | `main/support/ticket/{ticketId}` | from notification |
| `vulnmno://notifications` | `main/notifications` | from notification chip |

When the user is not authenticated and follows a deep link, the route is saved in `SavedStateHandle["pendingRoute"]` on `SCR-002 LoginScreen`. NAV-003 / NAV-006 consume it.

## Back-stack rules (recap)

1. **OTP back gesture** drops the challenge and returns to `SCR-002` with empty form.
2. **PurchaseConfirmation back** pops to `ShopScreen` (skips `Checkout` and `ProductDetail`).
3. **PlanChange success** pops to `PlansScreen`.
4. **Refund 202** pops to `TicketDetailScreen` (the ticket created for tracking).
5. **`401` from anywhere** clears the entire back-stack and resets to `LoginScreen`, saving the intended destination as `pendingRoute`.
6. **Logout** also clears the entire back-stack but discards `pendingRoute`.
7. **Bottom-nav tab switch** uses `saveState = true` so each tab keeps its own scroll position and nested back-stack.
