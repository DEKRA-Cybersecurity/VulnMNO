# Error codes (master enum)

## Scope

Single authoritative list of `error.code` values used across every VulnMNO endpoint. Every error response in `openapi.yaml` references one of these codes. Stage 04 generates a Python `Enum` from this list.

## Inputs consumed

- `02_api_contract/references/contract-rules.md` (error envelope).
- `01_requirements/output/backlog.md` (REQ-004, 005, 023, 024, 026, 044, 056 etc.).

## Findings

### Envelope

```json
{ "error": { "code": "PROMO_INELIGIBLE", "message": "…", "details": { "rule": "account_type" } } }
```

`code` is required, SCREAMING_SNAKE, drawn from the table below. `message` is required, free text intended for developers (not necessarily end-users). `details` is optional, an object whose contents are documented per code.

### Standard codes

| Code | HTTP | Used by | Description |
| --- | --- | --- | --- |
| `UNAUTHENTICATED` | 401 | all protected EPs | Bearer token missing, malformed, or signature invalid. |
| `TOKEN_EXPIRED` | 401 | all protected EPs | Access or refresh token expired. |
| `TOKEN_REVOKED` | 401 | EP-002, EP-003 | Refresh token revoked (logout, password reset, chain compromise). |
| `INVALID_CREDENTIALS` | 401 | EP-001 | Wrong MSISDN/password combination. Same code regardless of whether MSISDN exists. |
| `OTP_REQUIRED` | (n/a) | EP-001 happy-path | Not an error — emitted as `challenge: "OTP"` in the success body. Listed here for completeness. |
| `OTP_INVALID` | 401 | EP-004 | OTP code wrong or expired or attempts exhausted. |
| `NOT_FOUND` | 404 | all by-ID EPs | Resource does not exist, or exists but is owned by a different customer (REQ-203 — no existence leak). |
| `VALIDATION_FAILED` | 400 | all EPs with bodies | Request body or query parameters failed schema validation. `details.errors` is an array of `{loc, msg, type}`. |
| `RATE_LIMITED` | 429 | all EPs | Rate limit hit. `details.retryAfterSeconds` is set. Phase 1 declares the seam but does not enforce. |
| `CONFLICT` | 409 | EP-031, EP-043, EP-065 | Action incompatible with current resource state. |
| `INTERNAL` | 500 | all EPs | Unhandled server error. `message` is generic; full detail is server-side only. |

### Domain codes

| Code | HTTP | Used by | Description |
| --- | --- | --- | --- |
| `PROMO_INVALID` | 400 | EP-032, EP-033 | Promo code unknown, expired, or already consumed beyond `usageLimit`. |
| `PROMO_INELIGIBLE` | 400 | EP-032, EP-033 | Promo exists but customer is not eligible. `details.rule` ∈ {`account_type`, `prior_usage`, `plan_membership`, `loyalty_tier`}. |
| `INSUFFICIENT_BALANCE` | 409 | EP-033 | Wallet balance < `finalPrice`. `details.shortfall` and `details.currency` are set. |
| `PLAN_INELIGIBLE` | 400 | EP-042 | Target plan exists but customer is not eligible. `details.rule` ∈ {`account_type`, `loyalty_tier`, `geographic`}. |
| `PLAN_CHANGE_PENDING` | 409 | EP-042 | A pending plan change already exists; cancel it first via EP-043. |
| `TICKET_CLOSED` | 409 | EP-063, EP-064 | Action attempted on a closed ticket. |
| `IDEMPOTENCY_CONFLICT` | 409 | EP-022, EP-033, EP-042 | Same `Idempotency-Key` used with a different request body within the 24h window. |

### Stage 04 mapping

- Each code becomes a member of `app/errors.py::ErrorCode` (Python `StrEnum`).
- A single FastAPI exception handler maps `AppError(code, http_status, message, details)` to the envelope above.
- Pydantic validation errors are caught and re-emitted as `VALIDATION_FAILED` with `details.errors` populated from the original `ValidationError.errors()` output.

## Open questions

None.
