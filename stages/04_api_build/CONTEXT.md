# Stage 04 — API build (FastAPI)

Implement the backend so that every `EP-…` from stage 02 returns responses matching the OpenAPI spec, backed by the data model from stage 03.

## Inputs

**Layer 4 (working):**
- `../02_api_contract/output/openapi.yaml`
- `../02_api_contract/output/endpoints.md`
- `../02_api_contract/output/error-codes.md`
- `../02_api_contract/output/auth-model.md`
- `../03_data_model/output/entities.md`
- `../03_data_model/output/backend/` — models, initial migration, seed loader to move forward into the full backend.

**Layer 3 (reference):**
- `references/implementation-checklist.md` — per-endpoint-group implementation order and DoD.
- `../../_config/code-style.md` — Python project layout and style.
- `../../_config/tech-stack.md` — locked versions.
- `../../_config/conventions.md` — error envelope, ID format, currency, datetime.

## Process

1. Move/extend the model + migration + seed scaffolding from stage 03's `output/backend/` into this stage's `output/backend/`. From here onward, this folder is the canonical backend project.
2. Implement endpoint groups in the order defined in `references/implementation-checklist.md`. Each group:
   - Pydantic schemas in `app/schemas/` matching `openapi.yaml`.
   - Service module in `app/services/` for business logic.
   - Router module in `app/routers/`.
   - pytest module in `tests/` covering happy path + at least one error path per endpoint.
3. Implement the auth model exactly as described in `auth-model.md`: JWT issue + verify, refresh, OTP challenge.
4. The audit service (`app/services/audit.py`) writes one `AuditEvent` row per login, purchase, plan change, refund, ticket creation. Write-only, fire-and-forget; failures here must not fail the parent request (log + continue).
5. After all groups are implemented, export the FastAPI-generated OpenAPI to `output/openapi.generated.yaml` and **diff it against stage 02's `openapi.yaml`**. Any divergence is either fixed in stage 02 first (then re-pulled) or recorded as an intentional deviation in `output/contract-deltas.md`.
6. Keep `app/main.py` thin: app factory, router includes, lifespan handlers, OpenAPI title/version.

## Outputs

Under `output/`:

- `backend/` — full FastAPI project, runnable via `uvicorn app.main:app --reload`. README explains local run.
- `openapi.generated.yaml` — the spec actually served by FastAPI.
- `contract-deltas.md` — table of any divergence from stage 02's spec. Empty file (just headers) when there is none.
- `coverage-summary.md` — pytest coverage for `app/services/` and `app/routers/`. Target: ≥ 80% on routers, ≥ 90% on services.

## Definition of done for this stage

- `uvicorn` boots without errors against the seeded SQLite DB.
- `pytest -q` is green.
- `GET /api/customers/me` with a token issued by `POST /api/auth/login` for a seeded customer returns a payload matching the §13.1 example shape.
- `openapi.generated.yaml` ≡ `openapi.yaml` (or every diff is documented in `contract-deltas.md`).
