# API2 — Broken Authentication · VulnMNO Pentest Guide

This guide documents a **pre-existing** weakness in the VulnMNO backend. No
new code was added for this lab — it is the same root cause already
catalogued as [`M3 — Insecure Authentication/Authorization`](../mobile/M3-Insecure-Authentication-Authorization.md)
(OWASP Mobile Top 10), re-tagged here under the **OWASP API Security Top 10
(2023)** taxonomy, since it is directly relevant to an API-only assessment
that never touches the Android client.

> **Scope.** Pure HTTP. Every attack below is a request to `/api/auth/*` and
> needs no device, APK, or mobile tooling — see the M3 guide's own scope note.

OWASP API Security reference: **API2:2023 — Broken Authentication.**

| Lab | Subcategory | Severity | Difficulty | Full write-up |
|---|---|---|---|---|
| A | Login-OTP brute-force (no attempts cap) | High | Medium | [M3 L1](../mobile/M3-Insecure-Authentication-Authorization.md#l1--login-otp-code-brute-force-no-attempts-cap) |
| B | Password-reset brute-force → account takeover | Critical | Easy/Medium | [M3 L2](../mobile/M3-Insecure-Authentication-Authorization.md#l2--forgot-password-otp-brute-force--account-takeover) |

## Why this is API2, not (only) M3

The OWASP **Mobile** Top 10 (MASVS) and the OWASP **API Security** Top 10
classify the same server-side defect differently depending on which
assessment lens you use:

- As a **mobile app** finding, it's `M3 — Insecure Authentication/Authorization`:
  the client ships a login flow whose server doesn't actually protect it.
- As an **API** finding, it's `API2:2023 — Broken Authentication`: the token
  endpoints (`/api/auth/otp/verify`, `/api/auth/password-reset/confirm`)
  accept unlimited authentication attempts against a short, guessable
  secret (a 6-digit code), with no rate limiting and no lockout — regardless
  of which client calls them.

Same code, same exploitation mechanics, two different compliance mappings.
If your assignment is "cover the OWASP API Top 10", cite **this** document;
if it's "cover the OWASP Mobile Top 10", cite the M3 guide. Don't fix or
demo both as if they were independent bugs — one code change
(`app/services/auth.py::verify_otp`, `app/routers/auth.py::password_reset_confirm`)
remediates both labs.

## Where it lives

- `POST /api/auth/otp/verify` — `app/services/auth.py::verify_otp` (attempts
  cap deliberately removed, see the inline comment at `services/auth.py:94-104`)
- `POST /api/auth/password-reset/confirm` — `app/services/auth.py::confirm_password_reset`
  (no `@limiter.limit(...)`, and `PasswordReset` has no `attempts` column)

## How to find it (static analysis)

```bash
grep -n "otp_max_attempts\|attempts" src/backend/app/services/auth.py
grep -n "@limiter.limit" src/backend/app/routers/auth.py
```

The first command surfaces the comment admitting the cap was removed; the
second shows `@limiter.limit("5/minute")` on `/login` only — `/otp/verify`
and `/password-reset/confirm` carry no decorator, and `Limiter` has no
`default_limits` in `app/rate_limit.py`, so nothing throttles them globally
either.

## Dynamic exploitation

Full walk-throughs (manual, Burp Suite, ffuf/wfuzz, feasibility math, the
204-vs-401 oracle, and how to defeat the fixed lab codes so there's something
real to brute-force) live in the M3 guide — see
[L1](../mobile/M3-Insecure-Authentication-Authorization.md#l1--login-otp-code-brute-force-no-attempts-cap)
and
[L2](../mobile/M3-Insecure-Authentication-Authorization.md#l2--forgot-password-otp-brute-force--account-takeover).
They apply unmodified: point the same tooling at the same endpoints with
`curl`/`httpx` instead of the app, there is no mobile-specific step in either
lab.

## Blue-team detection

```sql
-- OTP: a challenge with an attempts count that never got capped
SELECT challenge_token, attempts, created_at
FROM otp_challenges
WHERE attempts > 20
ORDER BY attempts DESC;

-- Password reset: many reset requests for the same msisdn in a short window
SELECT customer_id, COUNT(*) AS requests, MIN(created_at), MAX(created_at)
FROM password_resets
GROUP BY customer_id
HAVING COUNT(*) > 5;
```

Backend logs also carry the issued codes for lab purposes
(`grep -E 'OTP|PWRESET' docker logs docker-backend-1`) — useful to prove what
*was* issued during an incident review, not to short-circuit the exercise.

## Remediation diff (sketch — not applied)

```diff
--- a/app/services/auth.py
+++ b/app/services/auth.py
@@ verify_otp
+    if challenge.attempts >= settings.otp_max_attempts:
+        raise AppError(ErrorCode.OTP_INVALID, "Too many attempts", http_status=401)
     challenge.attempts += 1
```

```diff
--- a/app/routers/auth.py
+++ b/app/routers/auth.py
@@
+@limiter.limit("5/minute")
 async def password_reset_confirm(...):
```

Plus: add an `attempts` column to `PasswordReset` and consume the row after
N failures, matching the OTP model's shape.
