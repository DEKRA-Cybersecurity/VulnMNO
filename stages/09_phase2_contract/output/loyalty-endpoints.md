# Loyalty endpoints (Phase 2 extension to customer-facing API)

## Scope

Two new public endpoints under `/api/loyalty/*`. Customer-facing, JWT-authenticated like the rest of `/api/*`. The mobile `AccountScreen` (SCR-007) gains a section consuming these.

## Inputs consumed

- `../08_phase2_requirements/output/backlog.md` (REQ-322, REQ-323)
- `../02_api_contract/output/endpoints.md` (style/conventions match)

## Findings

| ID | Method | Path | Auth | Request | Response | Errors | Journey |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-090 | GET | `/api/loyalty/account` | bearer | — | `LoyaltyAccountRead` | auth errors | cross-cutting |
| EP-091 | GET | `/api/loyalty/transactions` | bearer | `?limit&cursor` | `Page<LoyaltyTransactionRead>` | auth errors | cross-cutting |

## Schemas (added to `openapi.yaml`)

```yaml
LoyaltyAccountRead:
  type: object
  required: [customerId, points, lifetimePoints, tier, multiplier]
  properties:
    customerId: { type: string, pattern: '^CUST-[0-9]+$' }
    points: { type: integer, minimum: 0 }
    lifetimePoints: { type: integer, minimum: 0 }
    tier: { type: string, enum: [bronze, silver, gold, platinum] }
    multiplier:
      type: number
      format: decimal
      multipleOf: 0.01
      description: Points-per-EUR multiplier at the current tier.
    nextTier: { type: string, enum: [silver, gold, platinum], nullable: true }
    pointsToNextTier: { type: integer, minimum: 0, nullable: true }

LoyaltyTransactionRead:
  type: object
  required: [transactionId, accountId, delta, balanceAfter, reason, timestamp]
  properties:
    transactionId: { type: string, pattern: '^LTX-[0-9]+$' }
    accountId: { type: string, pattern: '^LACC-[0-9]+$' }
    delta:
      type: integer
      description: Positive on accrual, negative on redemption/adjustment.
    balanceAfter: { type: integer, minimum: 0 }
    reason: { type: string, enum: [purchase, tier_bonus, manual_adjust, expiration] }
    relatedPurchaseId: { type: string, nullable: true }
    timestamp: { type: string, format: date-time }
```

## Mobile consumption

`SCR-007 AccountScreen` is extended with a "Loyalty" section that calls `EP-090` on entry. A "View history" link navigates to a new screen `SCR-026 LoyaltyHistoryScreen` consuming `EP-091`. This is the smallest delta to existing screens (no new bottom-nav tab).

## Open questions

None.
