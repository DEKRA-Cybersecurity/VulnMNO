# API6 — Unrestricted Access to Sensitive Business Flows · VulnMNO Pentest Guide

This guide documents a **pre-existing** API6 weakness in the VulnMNO backend.
No code is added for this lab — it is already present and catalogued here so
trainees can practise locating, exploiting and remediating it.

> **Scope.** Backend only, pure HTTP. Needs a valid customer JWT. Exercises
> the §9.2 "Purchase of a data bundle (with promo)" journey directly.

OWASP API Security reference: **API6:2023 — Unrestricted Access to Sensitive
Business Flows.**

| Lab | Subcategory | Severity | Difficulty |
|---|---|---|---|
| L1 | Promo-code redemption has no per-customer cap | Medium | Easy |

## Where it lives

- **Endpoint:** `POST /api/shop/purchases` · body includes `promoCode`
- **Code:** `app/routers/shop.py:184-190` (coupon bump), `app/services/shop.py::resolve_promo`
- **Seed data:** `app/seed.py:202-234` (`PROMO-SUMMER-2026` / coupon `SUMMER20`, `usage_limit=10000`)

## Why it is API6

The business flow being protected is "redeem a promotional discount when
buying a bundle" (docs §9.2). Two independent checks exist, and neither
actually rate-limits *the same customer redeeming the same code repeatedly*:

1. **Global usage cap.** `resolve_promo` rejects once
   `coupon.usage_count >= coupon.usage_limit` (`services/shop.py:34`) — but
   this counter is shared across **every** customer, not scoped per account.
2. **Optional eligibility rule.** A promotion *can* carry
   `eligibility_rules: {"max_prior_purchases": N}`, which does cap reuse per
   customer — but it's opt-in per promotion. Only the seeded
   `PROMO-FIRST` / `WELCOME50` uses it (`app/seed.py:209`). The journey's
   main demo coupon, `SUMMER20` (`PROMO-SUMMER-2026`, `app/seed.py:224`,
   `usage_limit=10000`), carries no such rule.

Put together: one authenticated customer can call `POST /api/shop/purchases`
with `promoCode: "SUMMER20"` **repeatedly**, and get the 10% discount every
time, until the *shared, 10000-wide* pool is exhausted — with nothing tying
consumption to that one account. This is exactly the OWASP API6 pattern: a
legitimate, authenticated, individually-valid-looking business action
(redeem a promo) with no control over how many times *one actor* can trigger
it — enabling scripted abuse of promotional pricing at scale, not a one-off
discount bypass.

## How to find it (static analysis)

```bash
grep -n "usage_count\|usage_limit\|max_prior_purchases" src/backend/app/services/shop.py src/backend/app/routers/shop.py
grep -n "eligibility_rules" src/backend/app/seed.py
```

Confirms: `usage_count` is bumped and checked globally; only promotions whose
seed data explicitly sets `max_prior_purchases` get a per-customer limit.

## Dynamic exploitation

```bash
ACCESS_TOKEN="..."   # from /api/auth/login for +34600000001 / secret123
PRODUCT_ID="..."      # any productId from GET /api/shop/products

for i in $(seq 1 20); do
  curl -s -X POST http://localhost:8000/api/shop/purchases \
    -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json' \
    -d "{\"productId\":\"$PRODUCT_ID\",\"promoCode\":\"SUMMER20\"}" \
    | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("finalPrice"), d.get("purchaseId"))'
done
```

Every iteration succeeds at the same discounted `finalPrice` — nothing stops
the same customer from repeating this beyond ordinary balance/inventory
limits. Cross-check with:

```sql
SELECT customer_id, COUNT(*) AS redemptions
FROM purchases
WHERE promotion_id = (SELECT id FROM promotions WHERE public_id = 'PROMO-SUMMER-2026')
GROUP BY customer_id
ORDER BY redemptions DESC;
```

## Blue-team detection

```sql
-- Same customer redeeming the same coupon far more than a real shopper would
SELECT p.customer_id, c.code, COUNT(*) AS uses
FROM purchases p
JOIN coupons c ON c.promotion_id = p.promotion_id
WHERE p.status = 'confirmed'
GROUP BY p.customer_id, c.code
HAVING COUNT(*) > 3;
```

## Remediation diff (sketch — not applied)

```diff
--- a/app/services/shop.py
+++ b/app/services/shop.py
@@ resolve_promo
+    from app.models import Purchase
+    prior_same_coupon = (
+        await session.execute(
+            select(Purchase).where(
+                Purchase.customer_id == customer.id,
+                Purchase.promotion_id == promo.id,
+                Purchase.status == "confirmed",
+            )
+        )
+    ).scalars().all()
+    if len(prior_same_coupon) >= promo.max_uses_per_customer:  # new column, default 1
+        raise bad_request(ErrorCode.PROMO_INELIGIBLE, "Already redeemed", rule="per_customer_limit")
```

Add a `max_uses_per_customer` column to `Promotion` (default `1`) so every
promo — not just the ones that remember to set `max_prior_purchases` — gets a
per-account cap by default.
