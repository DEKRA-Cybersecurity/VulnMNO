# i18n keys catalog

Backend message catalog driven by `Accept-Language` header. en / es supported, en is the fallback. Lives in `app/i18n_catalog.yaml`; `app/i18n.py` loads + caches it. Android client uses standard `res/values/strings.xml` + `res/values-es/strings.xml`.

## Backend keys (English ↔ Spanish)

| Key | en | es |
| --- | --- | --- |
| `error.invalid_credentials` | Wrong phone number or password. | Número o contraseña incorrectos. |
| `error.otp_invalid` | OTP code is invalid or expired. | El código OTP no es válido o ha caducado. |
| `error.promo_invalid` | Promo code is not valid. | El código promocional no es válido. |
| `error.promo_ineligible` | You are not eligible for this promotion. | No reúnes los requisitos para esta promoción. |
| `error.insufficient_balance` | Wallet balance is too low for this purchase. | Saldo insuficiente para esta compra. |
| `error.plan_ineligible` | You are not eligible for this plan. | No puedes contratar este plan. |
| `error.payment_declined` | Your payment was declined by the gateway. | El pago ha sido rechazado por la pasarela. |
| `error.provisioning_failed` | Service activation failed. Please contact support. | Falló la activación del servicio. Contacta con soporte. |
| `error.rate_limited` | Too many requests. Please try again later. | Demasiadas peticiones. Vuelve a intentarlo más tarde. |
| `notification.purchase.title` | Purchase confirmed | Compra confirmada |
| `notification.plan_change.title` | Plan updated | Plan actualizado |
| `notification.low_balance.title` | Wallet running low | Saldo bajo |
| `notification.refund_approved.title` | Refund approved | Reembolso aprobado |

## Scope of i18n in Phase 2

- **JSON `AppError.message`:** mapped from `error.<code_lowercase>` when present; falls back to the English literal otherwise.
- **Notification titles:** Stage 12's `audit_hook` uses the English title from `_DISPATCH` for now; full i18n requires per-customer locale preference (Phase 3).
- **Admin portal templates:** English-only by design (internal staff tool).

## Android consumption

`stages/06_mobile_build/output/android/app/src/main/res/values/strings.xml` (English) +
`.../values-es/strings.xml` (Spanish) cover Auth, Home, Shop, and Loyalty sections.
Locale auto-selects from device language. Manual override is `OUT-OF-PHASE-2`.

## Verification (runtime)

```python
# Sends Accept-Language: es with wrong credentials
r = requests.post("/api/auth/login",
                  headers={"Accept-Language": "es"},
                  json={"msisdn":"+34600000001","password":"wrongwrong"})
assert r.status_code == 401
assert r.json()["error"]["message"] == "Número o contraseña incorrectos."
```

Confirmed during stage execution.
