# Stage 13 — Phase 2 integration & smoke

Produce E2E cases that exercise Phase 2 (admin portal, loyalty accrual, i18n, rate limiting), a curl-based admin smoke script, an extended docker-compose (Postgres + provisioning mock), and an updated repo-root README. Record the first Phase-2 pass in `run-log.md`.

## Inputs

**Layer 4 (working):**
- `../11_admin_portal_build/output/admin-screens-built.md`
- `../11_admin_portal_build/output/coverage-summary.md`
- `../12_integrations_and_ops/output/*.md`
- `../07_integration/output/*` (Phase 1 smoke + docker-compose to extend in place)

**Layer 3 (reference):**
- `../07_integration/references/e2e-rules.md`

## Process

1. Author Phase-2 INT cases (INT-200…) covering: admin login + balance adjust + audit visible, refund approve flow (wallet credited), agent reply on ticket, plan/promo creation, loyalty accrual visible to mobile app, rate-limit hit + recovery, i18n locale switch.
2. Write `scripts/smoke_admin.sh` using `curl --cookie-jar` for session cookies + form submits; asserts on status codes + HTML/text content. Exits non-zero on first failure.
3. Extend the Phase-1 `scripts/smoke_mobile.md` checklist with new sections for loyalty (points visible after purchase) and i18n (Spanish error messages).
4. Update `docker-compose.yml` adding `provisioning-mock` (a tiny FastAPI stub baked into the same image). Stripe and FCM mocks documented as `OUT-OF-PHASE-2` runtime — the dev driver suffices.
5. Update the repo-root `README.md` with a "Phase 2 quickstart" section (admin portal URL, seeded admin credentials, driver matrix, link to admin smoke).
6. Append the first Phase-2 run entry to `run-log.md`.

## Outputs

Stage-level outputs (`output/`):
- `e2e-cases.md` (Phase-1 INTs preserved + INT-200… new ones).
- `scripts/smoke_admin.sh` (executable).
- `scripts/smoke_mobile.md` extended.
- `docker-compose.yml` (extended).
- `run-log.md` appended.
- (Repo-root) `README.md` updated with Phase 2 section.
