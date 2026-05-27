# Stage 03 — Data model

Translate `docs/VulnMNO.md` §11 entities and the schemas from stage 02 into SQLAlchemy 2.x async ORM models, Alembic migrations and idempotent seed data.

## Inputs

**Layer 4 (working):**
- `../02_api_contract/output/openapi.yaml` — authoritative schema names and field shapes.
- `../02_api_contract/output/endpoints.md` — which entities are read and written by which endpoint.
- `../01_requirements/output/traceability.md` — for §11 ↔ §12 cross-references.

**Layer 3 (reference):**
- `references/entity-rules.md` — table naming, FK conventions, index policy, soft-delete policy, money/datetime mapping.
- `../../shared/glossary.md` — entity list.
- `../../_config/conventions.md` — `ENT-` IDs and `entities.md` shape.
- `../../_config/tech-stack.md` — SQLAlchemy 2.x async + Alembic.
- `../../_config/code-style.md` — Python project layout for `app/models/`.

## Process

1. For each §11 entity, assign an `ENT-…` ID and decide the table name (snake_case plural: `customers`, `mobile_lines`).
2. Map every API field used by stage 02's schemas to a column. Conversely: every column must be either (a) exposed in some `Read` schema, (b) FK glue, or (c) audit metadata (`created_at`, `updated_at`). No orphan columns.
3. Define relationships explicitly (`relationship(...)` with `back_populates`).
4. Generate Alembic migration scripts (one initial migration that creates the whole schema).
5. Produce idempotent seed data per `setup/questionnaire.md`: 3 customers, plans, bundles, promos, sample usage records, sample invoice, sample ticket.
6. Do **not** implement business logic. Constraints (uniqueness, non-null, FK on delete) yes; CHECK constraints for business rules no — those belong in stage 04 services.

## Outputs

Write to `output/`:

- `entities.md` — table per `_config/conventions.md` `Entities` shape, one row per `ENT-…`.
- `schema.sql` — annotated SQL dump of `CREATE TABLE` statements, generated from the SQLAlchemy metadata. Reference artifact for review.
- `backend/app/models/` — SQLAlchemy ORM modules (this folder will be moved into stage 04's `backend/` in stage 04; here it is generated and reviewed in isolation).
- `backend/alembic/versions/0001_initial.py` — initial migration.
- `backend/app/seed.py` — idempotent seed loader. Running it twice produces the same database.

Headers per `_config/report-style.md` are not required on code files but are required on `entities.md`.
