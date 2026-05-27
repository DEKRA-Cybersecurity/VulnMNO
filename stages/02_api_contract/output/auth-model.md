# Auth model

## Scope

Defines the authentication and session model for every VulnMNO endpoint in phase 1: token shapes, lifetimes, OTP challenge flow, refresh, password reset. Stage 04 implements this verbatim.

## Inputs consumed

- `01_requirements/output/backlog.md` (REQ-001…009, REQ-200…203).
- `02_api_contract/references/contract-rules.md` (authentication section).
- `docs/VulnMNO.md` §9.1, §12.1, §13.1.

## Findings

### Access token (JWT)

- **Algorithm:** HS256.
- **TTL:** 60 minutes.
- **Claims:**
  - `sub` — customer `public_id`, e.g. `"CUST-10001"`.
  - `iat` — issued at (Unix epoch seconds, UTC).
  - `exp` — expiry (Unix epoch seconds, UTC). `exp = iat + 3600`.
  - `jti` — opaque random 16-byte hex string. Used to revoke the access token on logout if needed (phase 1 does not maintain a revocation list for access tokens — `exp` is the only bound).
  - `typ` — literal `"access"`.
- **Signing key:** loaded from `JWT_SECRET` env var, ≥ 32 bytes.

### Refresh token

- **Format:** opaque 32 random bytes, base64url-encoded (no padding), length 43.
- **Storage:** server-side, hashed with SHA-256 in the `refresh_tokens` table. Plain value is returned to the client exactly once at issue time.
- **TTL:** 30 days from issue.
- **Rotation:** every successful `POST /api/auth/refresh` rotates: the presented refresh token is marked `revoked_at = now()` and a new one is issued. Re-using a revoked refresh token revokes the entire refresh-token chain for that customer (`REVOKED_CHAIN`) and returns `401 TOKEN_REVOKED`.
- **Revocation:** `POST /api/auth/logout` revokes the refresh token bound to the request's access token (via `jti`).
- **Password reset:** completing a password reset revokes **all** of the customer's refresh tokens.

### Login flow — non-OTP customer (REQ-001)

```
Client                                 Server
  | POST /api/auth/login                 |
  | { msisdn, password }                 |
  |------------------------------------->|
  |                                      | verify password
  |                                      | customer.otp_enrolled = false
  |                                      | issue access + refresh
  |<-------------------------------------|
  | 200 { accessToken, refreshToken,     |
  |       expiresIn, tokenType: "Bearer"}|
```

### Login flow — OTP-enrolled customer (REQ-002, REQ-003)

```
Client                                 Server
  | POST /api/auth/login                 |
  | { msisdn, password }                 |
  |------------------------------------->|
  |                                      | verify password
  |                                      | customer.otp_enrolled = true
  |                                      | generate challengeToken (opaque 32B b64url)
  |                                      | persist (customerId, challengeToken, expiresAt)
  |                                      | simulate-send OTP code to msisdn (log only)
  |<-------------------------------------|
  | 200 { challenge: "OTP",              |
  |       challengeToken,                |
  |       expiresIn: 300 }               |
  |                                      |
  | POST /api/auth/otp/verify            |
  | { challengeToken, code }             |
  |------------------------------------->|
  |                                      | look up challengeToken (≤ 5 min old)
  |                                      | verify code
  |                                      | delete challenge
  |                                      | issue access + refresh
  |<-------------------------------------|
  | 200 { accessToken, refreshToken,     |
  |       expiresIn, tokenType: "Bearer"}|
```

- **Challenge TTL:** 5 minutes (`docs/VulnMNO.md` §13.1).
- **Failed OTP attempts:** rate-limited at 5 attempts per challenge token; the 6th attempt invalidates the challenge and returns `OTP_INVALID`.
- **Simulated SMS in phase 1:** the OTP code is logged at `INFO` level by the simulated SMS sender. No real SMS is sent. Seeded test customers have a fixed OTP code (`123456`) for emulator testing.

### Refresh flow (REQ-006)

```
POST /api/auth/refresh
{ "refreshToken": "…" }

200 { accessToken, refreshToken, expiresIn, tokenType: "Bearer" }
```

The old refresh token is revoked atomically with the issue of the new one. If a revoked refresh token is presented, the entire chain is revoked and `401 TOKEN_REVOKED` is returned.

### Logout (REQ-007)

```
POST /api/auth/logout
Authorization: Bearer <access>

204
```

Revokes the refresh token associated with the access token's `jti`. Subsequent refresh attempts return `401 TOKEN_REVOKED`.

### Password reset (REQ-008, REQ-009)

```
POST /api/auth/password-reset/request
{ "msisdn": "+34600000001" }
204
```

- Always returns `204`, even for unknown MSISDNs, to avoid existence leaks.
- Generates a 6-digit numeric reset code, valid 15 minutes, single-use.
- Simulated SMS delivery (log only).

```
POST /api/auth/password-reset/confirm
{ "msisdn": "+34600000001", "code": "123456", "newPassword": "…" }
204
```

- Validates code; updates password (Argon2id hashing); revokes all refresh tokens for the customer.

### Authorization rule (REQ-200, REQ-202, REQ-203)

- Every endpoint except `/api/auth/*` requires `Authorization: Bearer <access>`.
- `me` in any path resolves from the access token's `sub` claim. Path/query `customerId` parameters are never trusted for scoping.
- Any resource lookup that returns a row not owned by `sub` returns `404 NOT_FOUND` — never `403` — to avoid existence leaks.

### Token errors (master codes from `error-codes.md`)

| Situation | HTTP | `error.code` |
| --- | --- | --- |
| Missing/malformed `Authorization` | 401 | `UNAUTHENTICATED` |
| Access token signature invalid | 401 | `UNAUTHENTICATED` |
| Access token expired | 401 | `TOKEN_EXPIRED` |
| Refresh token expired | 401 | `TOKEN_EXPIRED` |
| Refresh token revoked / reuse | 401 | `TOKEN_REVOKED` |
| OTP code wrong or expired | 401 | `OTP_INVALID` |
| Wrong password / unknown msisdn | 401 | `INVALID_CREDENTIALS` |

### Password storage

- Argon2id (`time_cost=3`, `memory_cost=64 MB`, `parallelism=4`).
- Library: `argon2-cffi`.

### Stored secrets

| Secret | Where | Notes |
| --- | --- | --- |
| `JWT_SECRET` | env var | ≥ 32 random bytes. |
| `argon2` parameters | code constant | Locked in phase 1. |
| Customer password hashes | `customers.password_hash` | Argon2id encoded string. |
| Refresh token hashes | `refresh_tokens.token_hash` | SHA-256, hex. |
| Reset code hashes | `password_resets.code_hash` | SHA-256, hex. |
| OTP challenge codes | `otp_challenges.code_hash` | SHA-256, hex. |

## Open questions

None for stage 02. Stage 04 will implement the lifespan-managed background task that purges expired refresh tokens, OTP challenges and reset codes.
