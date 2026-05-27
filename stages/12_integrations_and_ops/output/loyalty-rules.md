# Loyalty engine rules

## Tier table (seeded by `app/seed_phase2.py`)

| Tier | `threshold_lifetime_points` | `multiplier` (points-per-EUR) |
| --- | --- | --- |
| bronze | 0 | 1.00 |
| silver | 500 | 1.20 |
| gold | 2000 | 1.50 |
| platinum | 10000 | 2.00 |

## Accrual formula

On every successful `EP-033 create_purchase` (status='confirmed'), after the wallet debit and Transaction insert:

```
delta = int( purchase.final_price * tier_row.multiplier )
account.points += delta
account.lifetime_points += delta
LoyaltyTransaction(account_id, delta, balance_after, reason='purchase', related_purchase_id)
```

`int(...)` truncates (effectively floor) for predictable behavior. The multiplier is the customer's CURRENT tier multiplier (before any tier promotion this call may trigger).

## Tier promotion (one-way)

After accrual, the highest tier whose `threshold_lifetime_points ≤ lifetime_points` is computed. If it ranks higher than the current `account.tier` (per `_TIER_ORDER = ["bronze","silver","gold","platinum"]`), both `account.tier` and `customer.loyalty_tier` are updated.

**Downgrades never happen automatically.** A customer manually placed at `gold` (e.g. comped by ops_admin) stays at `gold` until they reach a higher threshold or an admin manually adjusts.

## Examples

| Initial tier | Purchase price | Multiplier | Delta | New `lifetime_points` | New tier |
| --- | --- | --- | --- | --- | --- |
| bronze (0 pts) | €7.99 | 1.00 | 7 | 7 | bronze |
| silver (0 pts) | €7.99 | 1.20 | 9 (round) → **10** | 10 | silver |
| bronze (495 pts) | €5.00 | 1.00 | 5 | 500 | **silver** (promoted) |
| gold (1500 pts) | €350.00 | 1.50 | 525 | 2025 | gold (already past 2000) |

> Note: Python's `Decimal.to_integral_value()` uses banker's rounding by default. `Decimal("9.588").to_integral_value()` → `10`. Stage 13's smoke uses 7.99 × 1.20 = 9.588 → **10 points** as the canonical test fixture.

## Endpoints

| EP | Method | Path | Returns |
| --- | --- | --- | --- |
| EP-090 | GET | `/api/loyalty/account` | `LoyaltyAccountRead` with `nextTier` + `pointsToNextTier` for the next-up tier. |
| EP-091 | GET | `/api/loyalty/transactions?limit=&cursor=` | `Page<LoyaltyTransactionRead>` ordered by `id` descending. |

## OUT-OF-PHASE-2

- **Redemption.** Spending points on discounts. Schema fields exist (`reason='manual_adjust'` could be repurposed), but no API surface.
- **Expiration.** Points never expire in Phase 2. `reason='expiration'` is reserved.
- **Customer-visible tier-up notification body.** Stage 12 promotes the tier internally; pushing a celebratory notification (`messageType=loyalty_tier_upgrade`) is wired in `audit_hook._DISPATCH` template but the producer that calls `write_audit(event_type="TIER_UPGRADED")` is not yet wired in `accrue_for_purchase`.

## Verification (runtime)

```python
# Customer with 0 points / silver tier (Alice, seeded).
r = requests.get("/api/loyalty/account", headers={"Authorization": f"Bearer {token}"})
assert r.json()["points"] == 0 and r.json()["tier"] == "silver"

# After buying DATA-10GB-7D with SUMMER20 (final 7.99):
r = requests.post("/api/shop/purchases", headers={...}, json={"productId":"DATA-10GB-7D","promoCode":"SUMMER20"})
assert r.status_code == 201

r = requests.get("/api/loyalty/account", headers={...})
assert r.json()["points"] == 10
assert r.json()["tier"] == "silver"  # not downgraded back to bronze
```

Confirmed during stage execution.
