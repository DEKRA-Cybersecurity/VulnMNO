# Entity rules

## Table naming

- `snake_case`, plural: `customers`, `mobile_lines`, `support_tickets`.
- Join tables use both parts plural: `customer_promotions`.
- Reserved word collisions: prefix with the entity (`audit_event`, not `event`).

## Primary keys

- Surrogate **integer** PK column named `id` for internal joins.
- A separate **public identifier** column (`public_id`, string, indexed, unique) that holds the §13-style prefixed ID (`CUST-10001`, `PUR-90001`). The API only ever exposes `public_id`. Never expose `id`.
- Generate `public_id` at insert time with a deterministic prefix per entity. Stage 04 picks the generator implementation; stage 03 just declares the column and uniqueness.

## Foreign keys

- FK columns named `<other_table_singular>_id` (`customer_id`, `account_id`).
- Always declare `ondelete` explicitly. Default to `RESTRICT` for financial integrity; `CASCADE` is allowed only for dependent rows that have no independent meaning (e.g. ticket messages cascade with their ticket).
- Always create an index on the FK column.

## Standard columns

Every table has:

```python
created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
```

Soft delete: only on `Customer`, `MobileLine`, `SIMProfile`, `SupportTicket` (`deleted_at: datetime | None`). Other tables hard-delete (or do not delete at all — `Transaction`, `AuditEvent`, `Invoice` are append-only).

## Money

- `Numeric(12, 2)` for monetary amounts. Never `Float`.
- Always pair with a `currency` column (3-char string) — even though phase 1 is EUR-only, the column reserves room.

## Datetime

- Stored as `TIMESTAMP WITH TIME ZONE` (or SQLite's ISO-8601 string equivalent). Application layer treats them as UTC-aware Python `datetime`.

## §11 → table mapping (recommended starting point)

| §11 entity | Table | Notes |
| --- | --- | --- |
| Customer | `customers` | Soft-delete. |
| Account | `accounts` | One per customer; could be merged in phase 1 but keep separate for fidelity to §11. |
| MobileLine | `mobile_lines` | Soft-delete. |
| SIMProfile | `sim_profiles` | Soft-delete. |
| Balance | `balances` | One row per account. Holds running balance. |
| Product | `products` | |
| Plan | `plans` | |
| Promotion | `promotions` | |
| Coupon | `coupons` | FK to `promotions`. |
| Purchase | `purchases` | Append-only after `confirmed`. |
| Transaction | `transactions` | Append-only. |
| Invoice | `invoices` | Append-only. |
| UsageRecord | `usage_records` | Append-only. Partitioning is out of phase 1 scope. |
| SupportTicket | `support_tickets` | Soft-delete. |
| TicketMessage | `ticket_messages` | Cascade with ticket. New — not in §11 explicitly but needed by §12.7. |
| Notification | `notifications` | |
| AuditEvent | `audit_events` | Append-only, no FK constraints (resilience to upstream changes). |

## Seed data rules

- The seed loader is **idempotent**: running it twice produces the same DB state.
- Use stable `public_id` values for seed rows (`CUST-10001`, `CUST-10002`, `CUST-10003`) so tests can reference them directly.
- Seed at least one row per table so every `GET` endpoint has a non-empty response.
