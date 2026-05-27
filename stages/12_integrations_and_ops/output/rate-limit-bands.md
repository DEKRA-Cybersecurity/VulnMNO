# Rate-limit bands

slowapi `Limiter(key_func=customer_or_ip)` configured in `app/rate_limit.py`. Hits return HTTP 429 with `{"error": {"code": "RATE_LIMITED", "message": <i18n>, "details": {"retryAfterSeconds": 60}}}` and a `Retry-After: 60` header.

## Bands (Phase 2)

| Endpoint | Limit | Key | Rationale |
| --- | --- | --- | --- |
| `POST /api/auth/login` | 5/minute | per-IP | Brute-force protection (REQ-300). |
| `POST /admin/login` | 5/minute | per-IP | Same — admin portal credential stuffing. |
| All other `/api/auth/*` | unlimited (Phase 2) | — | OTP / refresh / password-reset can be tightened in Phase 3. |
| `/api/shop/purchases` and `/api/accounts/me/topup` | unlimited (Phase 2) | — | Documented as future enforcement; idempotency-key already prevents double-charges. |
| Everything else | unlimited (Phase 2) | — | Default permissive. |

`VULNMNO_RATE_LIMIT_ENABLED=false` disables the entire limiter for tests. The `slowapi` middleware reads the `app.state.limiter` if and only if `rate_limit_enabled` is true at startup.

## Phase 3 extensions

- 10/min per-customer on `/api/shop/purchases` and `/api/accounts/me/topup`.
- 60/min per-customer default on all `GET /api/*` reads.
- Per-customer ban list (write to `audit_events` on repeated hits, fan out to security_analyst dashboard).

## Verification (runtime)

```python
for _ in range(7):
    requests.post("/api/auth/login", json={"msisdn":"+34600009999","password":"wrongwrong"})
# Statuses observed: [401, 401, 401, 401, 401, 429, 429]
```

Confirmed during stage execution.
