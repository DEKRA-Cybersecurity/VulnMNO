# Stage 08 — Phase 2 requirements & scope

Extend the Phase 1 backlog with everything OUT-OF-PHASE-1: admin portal journeys, payment-gateway integration, provisioning integration, FCM push delivery, agent replies on tickets, refund dispute workflow, internationalization, rate limiting, loyalty engine, campaign management automation. Produces a Phase-2 backlog, an updated traceability matrix, and the RBAC matrix that drives Stage 11.

## Inputs

**Layer 4 (working):**
- `../../docs/VulnMNO.md` — canonical product source (§7.13 admin portal, §8 roles, §13 assumptions).
- `../01_requirements/output/backlog.md` — Phase 1 backlog (OUT-OF-PHASE-1 section explicitly lists what this stage must cover).
- `../01_requirements/output/traceability.md`.

**Layer 3 (reference):**
- `../../_config/conventions.md` — extended here with new ID prefixes (`ADM-`, `AEP-`, `GW-`, `LOY-`) and Phase-2 row shapes.
- `../../shared/glossary.md` — admin role names, customer roles.
- `references/admin-journeys-template.md` — shape of an admin journey requirement.

## Process

1. Walk Phase 1 backlog's OUT-OF-PHASE-1 section. For each bullet, expand into REQ-200…REQ-2XX rows using **Given / When / Then** acceptance criteria.
2. Add admin journey requirements covering: login (cookie session), customer search, customer detail tabs (overview/lines/balance/transactions/purchases/plans/tickets), balance adjustment, plan CRUD, promotion + coupon CRUD, ticket triage and agent replies, refund approve/reject, audit log viewer, reporting dashboard, admin user management.
3. Add integration requirements: payment gateway (dev/stripe driver switch, idempotency forwarding, PAYMENT_DECLINED handling), provisioning (async retry, status surface), FCM push (delivery_status, notification row creation on customer-facing audit events).
4. Add ops requirements: rate limiting bands per endpoint group, i18n locales (es/en at minimum, header-driven), loyalty engine (points accrual, tier transitions, multipliers, redemption out of scope phase 2), campaign automation (auto-open/close based on dates).
5. Build the RBAC matrix — single source of truth for Stage 11's `@require_role` decorators.
6. Update the workspace's `_config/conventions.md` with the new ID prefixes and table shapes.

## Outputs

Write to `output/`:

- `backlog.md` — table per `_config/conventions.md` Requirements shape, REQ-200…REQ-2XX. Sectioned by feature block (admin journeys / payment / provisioning / FCM / agent replies / refund workflow / i18n / rate limiting / loyalty / campaigns). Opens with the standard four-section header.
- `traceability.md` — REQ-2XX → AEP-/EP- → ENT- → SCR-/ADM- mapping. Stage 09 consumes this to assign endpoint IDs.
- `admin-rbac-matrix.md` — 6 roles × ~10 admin modules; cells are `R`, `RW`, or `-`. Stage 11's permissions module is generated directly from this table.

All three files open with the four-section header (Scope / Inputs / Findings / Open questions).
