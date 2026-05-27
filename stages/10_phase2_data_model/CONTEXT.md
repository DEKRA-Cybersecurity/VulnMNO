# Stage 10 — Phase 2 data model

Add four new entities (AdminUser, LoyaltyAccount, LoyaltyTransaction, LoyaltyTier) and extend two existing tables (Notification.delivery_status/delivered_at, Transaction.gateway_charge_id, Purchase.provisioning_id). Produces SQLAlchemy models, an alembic migration `0002_phase2`, and an idempotent seed loader `seed_phase2`.

## Inputs

**Layer 4 (working):**
- `../09_phase2_contract/output/admin-endpoints.md`
- `../09_phase2_contract/output/loyalty-endpoints.md`
- `../09_phase2_contract/output/openapi.yaml`
- `../09_phase2_contract/output/adapter-interfaces.md`
- `../08_phase2_requirements/output/admin-rbac-matrix.md`

**Layer 3 (reference):**
- `../03_data_model/references/entity-rules.md` — same conventions: integer PK, `public_id` string, soft delete, timestamps, FK `RESTRICT` for financial integrity.
- `../../_config/code-style.md` — SQLAlchemy 2.x async patterns.

## Process

1. Extend `04_api_build/output/backend/app/models/` with:
   - `app/models/admin.py` — `AdminUser` (table `admin_users`).
   - `app/models/loyalty.py` — `LoyaltyAccount`, `LoyaltyTransaction`, `LoyaltyTier`.
   - Extend `app/models/notification.py` — `Notification.delivery_status` enum, `Notification.delivered_at` datetime.
   - Extend `app/models/transaction.py` — `Transaction.gateway_charge_id` string nullable.
   - Extend `app/models/purchase.py` — `Purchase.provisioning_id` string nullable.
2. Register new entities in `app/models/__init__.py`.
3. Bump alembic and autogenerate migration `0002_phase2`:
   ```bash
   cd stages/04_api_build/output/backend && python3 -m alembic revision --autogenerate -m "phase2" --rev-id 0002
   ```
4. Author `app/seed_phase2.py` extending Phase 1's `app.seed` patterns. Adds:
   - One AdminUser per role with seeded credentials documented in this stage's `entities-delta.md`.
   - Default LoyaltyTier rows (bronze 0/1.0, silver 500/1.2, gold 2000/1.5, platinum 10000/2.0).
   - LoyaltyAccount rows for each of the 3 seeded customers, all starting at 0 points.
5. Ensure idempotency: re-running `python -m app.seed_phase2` produces identical row counts.

## Outputs

Write to `output/`:

- `entities-delta.md` — table per `_config/conventions.md` Entities shape, plus the seed credentials table (admin usernames + plaintext seed passwords, since training-only).
- `schema-delta.sql` — generated `CREATE TABLE` for the new tables + `ALTER TABLE ADD COLUMN` for the extensions, dumped from `Base.metadata` post-extension.
- The backend source files are committed in-place into `04_api_build/output/backend/` (not copied here).

The `entities-delta.md` opens with the four-section header.
