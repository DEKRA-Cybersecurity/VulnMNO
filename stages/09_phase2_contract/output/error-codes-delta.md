# Error codes — Phase 2 delta

## Scope

Six new codes added to the master enum from `stages/02_api_contract/output/error-codes.md`. Stage 11 (admin) and Stage 12 (gateways) raise these. Mobile client mapping in `data/remote/ApiResult.kt` extended to surface them as `AppError.Domain`.

## Inputs consumed

- `../02_api_contract/output/error-codes.md` (existing 17 codes).
- `../08_phase2_requirements/output/backlog.md` (REQ-204, REQ-203, REQ-271, REQ-281, REQ-291).

## Findings

### New codes

| Code | HTTP | Used by | Description | `details` keys |
| --- | --- | --- | --- | --- |
| `ADMIN_FORBIDDEN` | 403 | all `/admin/*` mutating endpoints | The authenticated admin's role does not grant the required permission on this module; or CSRF token invalid. | `module`, optionally `required` |
| `ADMIN_SESSION_EXPIRED` | 401 | every protected `/admin/*` endpoint | Cookie session missing or expired. The HTML response is a 302 to `/admin/login?next=…` instead of a JSON body; the code exists for HTMX clients that intercept 401. | — |
| `PAYMENT_DECLINED` | 409 | EP-022 (topup), EP-033 (purchase) when `StripePaymentGateway` returns `error_code="card_declined"` or `insufficient_funds`. | `reason`, `gateway_status` |
| `PROVISIONING_FAILED` | 503 | EP-033 (purchase) post-confirm if all retries exhausted. Customer-facing: the purchase already shows status `confirmed` but provisioning `failed`. | `attempts`, `last_error` |
| `PUSH_FAILED` | 502 | `EP-072 register_device_token` — only when an immediate verification push fails. Not raised by the background push-on-audit-hook (that just marks the Notification row `delivery_status='failed'`). | `provider_error_code` |
| `LOYALTY_INSUFFICIENT_POINTS` | 409 | reserved for Phase 3 redemption. Declared now so the master enum is forward-compatible. | `required`, `available` |

### Updated standard mapping table

| Situation | HTTP | `error.code` |
| --- | --- | --- |
| (existing 17 codes from Phase 1) | … | … |
| Admin without permission | 403 | `ADMIN_FORBIDDEN` |
| Admin session expired (HTMX request) | 401 | `ADMIN_SESSION_EXPIRED` |
| Payment gateway declines | 409 | `PAYMENT_DECLINED` |
| Provisioning fails after retries | 503 | `PROVISIONING_FAILED` |
| Push delivery fails on registration | 502 | `PUSH_FAILED` |
| Loyalty redemption not affordable (Phase 3) | 409 | `LOYALTY_INSUFFICIENT_POINTS` |

### Mobile client mapping

`stages/06_mobile_build/output/android/app/src/main/java/com/vulnmno/app/data/remote/ApiResult.kt` parses `error.code` into `AppError.Domain`. Phase 2 needs no code changes there — the existing parsing already handles arbitrary `code` strings; only the UI mappings in the `userMessage()` extension benefit from new entries (Stage 12 / mobile i18n step).

## Open questions

None.
