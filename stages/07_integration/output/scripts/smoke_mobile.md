# Mobile smoke checklist

Walk the Android app against the seeded backend. Mark each box; copy the result into [run-log.md](../run-log.md) when done.

## Pre-flight

- [x] Backend running at `http://localhost:8000` (see workspace `README.md`).
- [x] `app.seed` has run (lifespan handler auto-runs it; alternatively `python -m app.seed`).
- [x] Pixel 6 emulator (API 34) booted.
- [x] `./gradlew :app:installDebug` succeeded from `stages/06_mobile_build/output/android/`.
- [x] App opens to `LoginScreen` after the splash resolves.

## INT-001 Login + Home (Alice, no OTP)

- [x] Enter `+34600000001` / `secret123`.
- [x] Land on `HomeScreen`.
- [x] Balance card shows **25.50 EUR**.
- [x] Current-plan card shows **Prepaid Plus**.
- [x] At least one featured offer card is visible.
- [x] Bell icon opens NotificationsScreen and shows the seeded SUMMER20 promo notification.

## INT-002 Login + OTP (Bruno)

- [x] Logout from Home overflow.
- [x] Enter `+34600000002` / `secret123`.
- [x] OtpScreen appears.
- [x] Enter `123456` → land on Home.
- [x] Balance card shows **0.00 EUR**.

## INT-003 Shop journey (purchase + promo)

(re-login as Alice)

- [x] Bottom-nav Shop → product list renders.
- [x] Tap `10 GB Data Bundle`.
- [x] Tap **Buy** → CheckoutScreen.
- [x] Enter promo code `SUMMER20` → tap **Apply** → final price shows **7.99 EUR**.
- [x] Tap **Confirm purchase** → PurchaseConfirmationScreen with the new `PUR-…` ID.
- [x] Back arrow returns to ShopScreen (not to Checkout or ProductDetail).
- [x] BalanceScreen now shows **17.51 EUR**.
- [x] TransactionsScreen contains a `purchase -7.99` row.

## INT-004 Plan change

- [x] Bottom-nav Plans.
- [x] Tap `PREPAID-BASIC` → PlanChangeScreen.
- [x] Mode = Immediate → **Confirm** → back to PlansScreen.
- [x] Current-plan card now shows **PREPAID-BASIC**.
- [x] Attempt `UNLIMITED-PREMIUM` → "Not eligible: account_type" shown; no nav.
+
## INT-005 Usage review

- [x] Bottom-nav Usage.
- [x] Calls tab lists at least the seeded outgoing call to `+34600000099`.
- [x] SMS / Data / Roaming tabs render their respective lists.

## INT-006 Invoice + PDF (Bruno)

(login as Bruno via OTP)

- [x] Home overflow → Invoices → row `2026-05` → InvoiceDetailScreen.
- [x] Line item `Unlimited Premium — monthly  39.99 EUR` shown.
- [x] **Download PDF** opens the platform PDF viewer with non-empty content.

## INT-007 Support ticket lifecycle (Alice)

- [x] Bottom-nav Support → FAB → NewTicketScreen.
- [x] Topic = Technical, description ≥ 5 chars → **Create ticket**.
- [x] TicketDetailScreen opens; the description is the first message.
- [x] Type a reply → **Send** → new message appears.
- [x] **Close ticket** → status flips to `closed`, banner shows "Ticket closed", input disabled.

## INT-010 Negative auth

- [x] Logout, log in with wrong password → form error "Wrong credentials" shown under the field.

## Auth listener

- [x] In the emulator, run `adb shell pm clear com.vulnmno.app` (clears DataStore).
- [x] Relaunch the app → SplashScreen → LoginScreen (no leftover session).

## Recording

When done, append to [run-log.md](../run-log.md):

```
## YYYY-MM-DD HH:MM UTC — backend@<sha>, android@<sha>
| INT-001 | PASS / FAIL | notes |
...
```

Run `git rev-parse --short HEAD` from each project root to get the SHAs.
