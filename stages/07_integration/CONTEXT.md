# Stage 07 — Integration & end-to-end

Validate that the backend (stage 04) and the Android app (stage 06) work together for every §9 journey. Produce a runnable workspace-level README and an end-to-end test plan.

## Inputs

**Layer 4 (working):**
- `../04_api_build/output/backend/` — runnable FastAPI project.
- `../04_api_build/output/openapi.generated.yaml`
- `../04_api_build/output/contract-deltas.md`
- `../06_mobile_build/output/android/` — runnable Android project.
- `../06_mobile_build/output/screens-built.md`
- `../01_requirements/output/backlog.md` — for journey acceptance criteria.

**Layer 3 (reference):**
- `references/e2e-rules.md` — what counts as a journey passing, how to record results, smoke-script conventions.
- `../../_config/conventions.md` — `INT-` IDs and `e2e-cases.md` shape.
- `../../setup/questionnaire.md` — local run config.

## Process

1. Reconcile contracts. If `04_api_build/output/contract-deltas.md` is non-empty, fix the spec in stage 02 (re-running stage 02 → 04) or document the accepted deltas here. The app must not silently work around them.
2. Write one `INT-…` case per §9 journey: login, purchase (with promo), plan change, usage review, invoice review (open + download), support ticket lifecycle (create, comment, close). Each case is a sequence of `(SCR-…, EP-…)` pairs with expected outcomes.
3. Implement two smoke scripts in `output/scripts/`:
   - `smoke_api.sh` — `curl`-based smoke for every endpoint group (authenticate, then one happy-path call per group). Exits non-zero on any failure.
   - `smoke_mobile.md` — manual checklist for the emulator pass (the Android UI test suite from stage 06 covers per-screen; this is the cross-journey checklist).
4. Author a `docker-compose.yml` for the `prod-like` profile (PostgreSQL + backend container). The Android emulator continues to point at host loopback.
5. Author the workspace-level `README.md` at the **repo root**: prerequisites, how to boot backend, how to boot emulator, how to run smoke scripts, how to interpret stage outputs. This is the file a new contributor reads first.
6. Run every `INT-…` case manually (or scripted where possible) and record pass / fail with timestamp + commit SHA in `output/run-log.md`.

## Outputs

Under `output/`:

- `e2e-cases.md` — table per `_config/conventions.md` `Integration tests` shape.
- `scripts/smoke_api.sh` — backend smoke script.
- `scripts/smoke_mobile.md` — emulator checklist.
- `docker-compose.yml` — `prod-like` profile.
- `run-log.md` — historical record of integration runs.

At the **repo root** (the only stage that writes outside `output/`):

- `README.md` — workspace-level run instructions.

## Definition of done for phase 1

Phase 1 is done when every journey §9.1–§9.6 has a passing `INT-…` row in `run-log.md` against the seeded backend, executed from the Android emulator. The README at the repo root is sufficient for a new contributor to reproduce the run without reading anything else.
