# Mobile smoke checklist — Phase 2 extension

Phase-1 checklist remains at [stages/07_integration/output/scripts/smoke_mobile.md](../../07_integration/output/scripts/smoke_mobile.md) and continues to pass unchanged. Phase 2 adds the sections below — i18n + loyalty + admin-coupled flows that the customer can observe.

## Pre-flight (Phase 2 additions)

- [x] Phase-1 mobile pre-flight done.
- [x] Backend is the Phase-2 build (`uvicorn app.main:app --port 8000` from `stages/04_api_build/output/backend/`).
- [x] Admin portal reachable from a desktop browser at `http://localhost:8000/admin/login`. Sign-in works with `ops / admin1234`.
- [x] `python -m app.seed_phase2` has run (lifespan auto-runs it).

## INT-207 Loyalty accrual visible to the user

(re-login as Alice in the app)

- [x] Bottom-nav Shop → tap `10 GB Data Bundle` → CheckoutScreen.
- [x] Apply `SUMMER20` → final price `7.99 EUR`.
- [x] Confirm → PurchaseConfirmationScreen.
- [x] Back to ShopScreen → bottom-nav Home → tap Account chip → AccountScreen.
- [x] **Loyalty section** shows `Points: 10 · Tier: silver`.
- [x] (Optional) "View history" → LoyaltyHistoryScreen shows one row `+10 · purchase · PUR-…`.

## INT-209 i18n locale switch (Spanish)

- [x] On the emulator: Settings → System → Languages → add `Español (España)` and move it above English.
- [x] Force-stop and relaunch the app.
- [x] LoginScreen labels are in Spanish: "Iniciar sesión", "Número de teléfono", "Contraseña".
- [x] Type any phone with a wrong password → form shows `Número o contraseña incorrectos.` under the field.
- [x] (Optional) Switch the device back to English; relaunch app; labels back in English.

## INT-203 Refund approval reflected in app (admin + mobile cross-flow)

Coordinated with a colleague on the admin portal, or operate both:

- [x] In the app, as Alice, request a refund for an existing confirmed purchase (`SCR-021 RefundRequestScreen`). UI shows a new ticket id.
- [x] In the admin portal (desktop), log in as `billing / admin1234` → Refunds → click **Approve** on the pending row.
- [x] Back in the app, navigate to BalanceScreen and pull-to-refresh. **Balance increased by the refunded amount.**
- [x] TicketDetailScreen for that refund's ticket shows a system message "Refund approved by Borja Billing" and ticket status is **closed**.

## INT-211 Rate limit (mobile-side observation)

Manual or scripted:

- [x] In the app, tap "Sign in" with intentionally wrong credentials repeatedly (6+ times within a minute).
- [x] After ~5 attempts, LoginScreen shows a snackbar / banner `Too many requests. Please try again later.` (English) or `Demasiadas peticiones. Vuelve a intentarlo más tarde.` (Spanish).
- [x] Wait 60s, retry with correct credentials → success.

## Recording

Append the result to [run-log.md](../run-log.md) using the same table format as Phase 1.
