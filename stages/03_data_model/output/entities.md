# Data model — entities

## Scope

SQLAlchemy 2.x ORM models, Alembic initial migration, and idempotent seed loader for VulnMNO phase 1. Every entity from `docs/VulnMNO.md` §11 maps to a row below, plus extras required by stage 02 (`TicketMessage`, `TicketAttachment`, `Refund`, `PlanChange`, `RefreshToken`, `OtpChallenge`, `PasswordReset`, `IdempotencyKey`, `DeviceToken`, `CustomerService`, `InvoiceLineItem`).

## Inputs consumed

- `02_api_contract/output/openapi.yaml` — schema names and field shapes.
- `02_api_contract/output/endpoints.md` — entity-to-endpoint mapping.
- `02_api_contract/output/auth-model.md` — auth/session tables.
- `01_requirements/output/traceability.md`.
- `_config/code-style.md`, `_config/tech-stack.md`, `_config/conventions.md`.
- `03_data_model/references/entity-rules.md`.

## Findings

### Entity table

| ID | Table | Columns (short) | PK / FK | Indexes | Source (§11) |
| --- | --- | --- | --- | --- | --- |
| ENT-001 | `customers` | id, public_id, name, email, primary_msisdn, account_type, status, loyalty_tier, password_hash, otp_enrolled, otp_fixed_code, last_login_at, billing_address (json), notification_preferences (json), created_at, updated_at, deleted_at | PK id; UQ public_id, primary_msisdn | (defaults) | Customer |
| ENT-002 | `customer_services` | id, customer_id, service_id, created_at, updated_at | PK id; FK customer_id (CASCADE) | ix_customer_services_customer_id | (new) |
| ENT-003 | `accounts` | id, public_id, customer_id, account_type, billing_status, created_at, updated_at | PK id; UQ public_id, customer_id; FK customer_id (RESTRICT) | ix_accounts_customer_id | Account |
| ENT-004 | `balances` | id, account_id, amount, currency, last_updated, created_at, updated_at | PK id; UQ account_id; FK account_id (CASCADE) | (defaults) | Balance |
| ENT-005 | `sim_profiles` | id, public_id, iccid, imsi_alias, sim_type, status, activation_date, created_at, updated_at, deleted_at | PK id; UQ public_id, iccid | (defaults) | SIMProfile |
| ENT-006 | `mobile_lines` | id, public_id, msisdn, customer_id, plan_id, sim_id, status, activated_at, created_at, updated_at, deleted_at | PK id; UQ public_id, msisdn, sim_id; FK customer (RESTRICT), plan (SET NULL), sim (SET NULL) | ix_mobile_lines_customer_id, ix_mobile_lines_plan_id | MobileLine |
| ENT-007 | `plans` | id, public_id, name, description, monthly_price, currency, data_limit_mb, voice_limit_min, sms_limit, category, eligibility_rules (json), available_services (json), created_at, updated_at | PK id; UQ public_id | (defaults) | Plan |
| ENT-008 | `plan_changes` | id, public_id, customer_id, from_plan_id, to_plan_id, mode, status, effective_date, applied_at, created_at, updated_at | PK id; UQ public_id; FK customer (RESTRICT), from_plan (RESTRICT), to_plan (RESTRICT) | ix_plan_changes_customer_id, ix_plan_changes_status | (new — derived from EP-042) |
| ENT-009 | `products` | id, public_id, name, description, category, price, currency, validity_days, eligible_plans (json), featured, availability, created_at, updated_at | PK id; UQ public_id | (defaults) | Product |
| ENT-010 | `promotions` | id, public_id, name, description, discount_type, discount_value, currency, starts_at, ends_at, eligibility_rules (json), eligible_product_ids (json), combinable, created_at, updated_at | PK id; UQ public_id | (defaults) | Promotion |
| ENT-011 | `coupons` | id, code, promotion_id, status, usage_limit, usage_count, created_at, updated_at | PK id; UQ code; FK promotion_id (CASCADE) | ix_coupons_promotion_id | Coupon |
| ENT-012 | `purchases` | id, public_id, customer_id, product_id, promotion_id, status, original_price, final_price, currency, provisioning_status, provisioning_activated_at, created_at, updated_at | PK id; UQ public_id; FK customer (RESTRICT), product (RESTRICT), promotion (SET NULL) | ix_purchases_customer_id_created_at, ix_purchases_status | Purchase |
| ENT-013 | `refunds` | id, public_id, customer_id, target_type, target_public_id, reason, status, ticket_id, created_at, updated_at | PK id; UQ public_id; FK customer (RESTRICT), ticket (SET NULL) | ix_refunds_customer_id | (new — derived from EP-026) |
| ENT-014 | `transactions` | id, public_id, account_id, type, amount, currency, balance_after, related_purchase_id, related_invoice_id, timestamp, created_at, updated_at | PK id; UQ public_id; FK account (RESTRICT), purchase (SET NULL), invoice (SET NULL) | ix_transactions_account_id_timestamp, ix_transactions_type | Transaction |
| ENT-015 | `invoices` | id, public_id, account_id, period, total_amount, currency, status, issued_at, created_at, updated_at | PK id; UQ public_id; FK account (RESTRICT) | ix_invoices_account_id_period, ix_invoices_status | Invoice |
| ENT-016 | `invoice_line_items` | id, invoice_id, description, amount, currency, related_product_public_id, related_plan_public_id, created_at, updated_at | PK id; FK invoice_id (CASCADE) | ix_invoice_line_items_invoice_id | (new — stage 02 resolution) |
| ENT-017 | `usage_records` | id, public_id, line_id, type, direction, destination, started_at, duration_seconds, volume_megabytes, country, network_type, roaming, cost, currency, created_at, updated_at | PK id; UQ public_id; FK line_id (RESTRICT) | ix_usage_records_line_id_started_at, ix_usage_records_type | UsageRecord |
| ENT-018 | `support_tickets` | id, public_id, customer_id, topic, description, status, last_updated_at, created_at, updated_at, deleted_at | PK id; UQ public_id; FK customer (RESTRICT) | ix_support_tickets_customer_id_created_at, ix_support_tickets_status | SupportTicket |
| ENT-019 | `ticket_messages` | id, public_id, ticket_id, author_role, author_display_name, body, created_at, updated_at | PK id; UQ public_id; FK ticket_id (CASCADE) | ix_ticket_messages_ticket_id | (new — required by §12.7) |
| ENT-020 | `ticket_attachments` | id, public_id, ticket_id, filename, size_bytes, content_type, storage_path, created_at, updated_at | PK id; UQ public_id; FK ticket_id (CASCADE) | ix_ticket_attachments_ticket_id | (new — required by §12.7) |
| ENT-021 | `notifications` | id, public_id, customer_id, channel, message_type, title, body, read_at, created_at, updated_at | PK id; UQ public_id; FK customer (CASCADE) | ix_notifications_customer_id_created_at | Notification |
| ENT-022 | `device_tokens` | id, customer_id, token, platform, app_version, last_seen_at, created_at, updated_at | PK id; UQ token; FK customer (CASCADE) | ix_device_tokens_customer_id | (new — EP-072) |
| ENT-023 | `audit_events` | id, event_type, actor_id, target_type, target_id, payload (json), ip_address, timestamp | PK id; no FKs (append-only resilience) | ix_audit_events_actor_id_timestamp, ix_audit_events_event_type | AuditEvent |
| ENT-024 | `refresh_tokens` | id, customer_id, token_hash, parent_id, access_jti, expires_at, revoked_at, revoked_reason, created_at, updated_at | PK id; UQ token_hash; FK customer (CASCADE), parent_id (SET NULL) | ix_refresh_tokens_customer_id, ix_refresh_tokens_expires_at | (auth-model.md) |
| ENT-025 | `otp_challenges` | id, customer_id, challenge_token, code_hash, attempts, expires_at, consumed_at, created_at, updated_at | PK id; UQ challenge_token; FK customer (CASCADE) | ix_otp_challenges_expires_at | (auth-model.md) |
| ENT-026 | `password_resets` | id, customer_id, code_hash, expires_at, consumed_at, created_at, updated_at | PK id; FK customer (CASCADE) | ix_password_resets_expires_at | (auth-model.md) |
| ENT-027 | `idempotency_keys` | id, customer_id, key, endpoint, request_hash, response_status, response_body, expires_at, created_at, updated_at | PK id; UQ (customer_id, endpoint, key); FK customer (CASCADE) | ix_idempotency_keys_expires_at | (auth-model.md) |

Total tables: **27** (verified via `Base.metadata.sorted_tables`).

### Deviations / extensions vs §11

- **`TicketMessage`, `TicketAttachment`** — required by §12.7 (messages and attachments endpoints) but not enumerated in §11. Documented above.
- **`InvoiceLineItem`** — stage 02 resolved Open question #3 by making it a separate entity.
- **`Refund`** — stage 02 resolved Open question #2; tracked as its own row plus a linked `SupportTicket` (per EP-026 returning a `ticketId`).
- **`PlanChange`** — surfaced by EP-042's `PlanChangeRead` schema (`changeId`, `status`, `effectiveDate`).
- **`DeviceToken`** — EP-072 endpoint. Stored, not delivered (phase 1).
- **`CustomerService`** — backs `PlanRead.activeServices` and EP-044/045 add/remove flows. Lookup of available services lives in `plans.available_services` JSON.
- **Auth-tier tables** (`refresh_tokens`, `otp_challenges`, `password_resets`, `idempotency_keys`) — required by `02_api_contract/output/auth-model.md`. Not in §11 because they are infrastructure, not domain.

### Public ID format (per `entity-rules.md`)

Every customer-visible entity exposes a prefixed string `public_id` that matches `docs/VulnMNO.md` §13 examples:

| Entity | Prefix | Example |
| --- | --- | --- |
| Customer | `CUST-` | `CUST-10001` |
| Account | `ACC-` | `ACC-10001` |
| MobileLine | `LINE-` | `LINE-10001` |
| SIMProfile | `SIM-` | `SIM-10001` |
| Product | `<category>-…` | `DATA-10GB-7D` |
| Plan | `<name>` | `PREPAID-PLUS` |
| Promotion | `PROMO-` | `PROMO-SUMMER-2026` |
| Purchase | `PUR-` | `PUR-90001` |
| Transaction | `TX-` | `TX-50001` |
| Invoice | `INV-` | `INV-20001` |
| UsageRecord | `USG-` | `USG-70001` |
| SupportTicket | `TCK-` | `TCK-30001` |
| TicketMessage | `MSG-` | `MSG-40001` |
| TicketAttachment | `ATT-` | `ATT-60001` |
| Notification | `NTF-` | `NTF-50001` |
| PlanChange | `PCH-` | `PCH-10001` |
| Refund | `REF-` | `REF-10001` |

Integer `id` columns are internal only; never serialized.

### Seed data

`app/seed.py` is idempotent (`_get_or_create` primitive). It loads:

- **4 plans:** `PREPAID-BASIC`, `PREPAID-PLUS`, `UNLIMITED-PREMIUM`, `STUDENT-25`.
- **4 products:** `DATA-10GB-7D` (featured), `DATA-5GB-30D`, `ROAMING-EU`, `VOICE-200MIN`.
- **3 promotions / 3 coupons:** `SUMMER20` (20% any data bundle, combinable), `GOLD10` (10% gold/platinum only), `WELCOME50` (50% first-purchase only).
- **3 customers** with one mobile line + SIM each:
  - `CUST-10001` Alice García — prepaid, silver, OTP off, balance €25.50, plan `PREPAID-PLUS`.
  - `CUST-10002` Bruno López — postpaid, gold, **OTP on (fixed code `123456`)**, balance €0.00, plan `UNLIMITED-PREMIUM`.
  - `CUST-10003` Clara Núñez — hybrid, bronze, OTP off, balance €12.00, plan `STUDENT-25`.
- **4 usage records** for `LINE-10001` in May 2026 (call, sms, data, roaming).
- **1 invoice** `INV-20001` for `CUST-10002` covering period `2026-05` with one line item.
- **1 support ticket** `TCK-30001` (billing dispute) opened by `CUST-10001` with one initial message.
- **1 in-app notification** advertising `SUMMER20` to `CUST-10001`.

Seed password is `secret123` for every test customer. Hash is a deterministic SHA-256 with a fixed salt (`seed$<hex>`); stage 04 swaps in Argon2id and may accept both formats during a one-time migration window before deleting `seed$`.

### Run / verify (locally)

```bash
cd stages/03_data_model/output/backend
python -m alembic upgrade head        # creates dev.db with the schema
python -m app.seed                    # idempotent; run again, same row counts
```

Expected row counts after either run:

| Table | Count |
| --- | --- |
| customers | 3 |
| accounts | 3 |
| balances | 3 |
| mobile_lines | 3 |
| plans | 4 |
| products | 4 |
| promotions | 3 |
| coupons | 3 |
| usage_records | 4 |
| invoices | 1 |
| invoice_line_items | 1 |
| support_tickets | 1 |
| ticket_messages | 1 |
| notifications | 1 |

## Open questions

None remaining for stage 03. Stage 04 owns:

- Argon2id rollout and the `seed$` migration window.
- The `public_id` generator implementations (currently fixed strings in seed; runtime generation needed for inserts from API).
- The lifespan background task that purges expired `refresh_tokens`, `otp_challenges`, `password_resets`, and `idempotency_keys` rows.
- Filesystem layout for `ticket_attachments.storage_path` under `output/backend/uploads/{customerId}/{ticketId}/`.
