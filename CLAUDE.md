# VulnMNO Build Workspace — Layer 0 (Identity)

You are working inside an **MWP (Model Workspace Protocol)** workspace whose purpose is to **build the VulnMNO platform**: a backend REST API and an Android mobile application, derived from the product description in [docs/VulnMNO.md](docs/VulnMNO.md).

## Phase 1 scope

Implement all six customer journeys from `docs/VulnMNO.md` §9:

1. §9.1 Login and account overview
2. §9.2 Purchase of a data bundle (with promo)
3. §9.3 Plan change
4. §9.4 Usage review
5. §9.5 Invoice review
6. §9.6 Support request

The corresponding API surface is §12 (endpoints) and §13 (request/response examples). The data model is §11.

## Tech stack (fixed)

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, Uvicorn. SQLite for local development; PostgreSQL-compatible.
- **Mobile:** Android (minSdk 26), Kotlin, Jetpack Compose, Retrofit + Kotlinx Serialization, Hilt for DI, Coroutines + Flow, Material 3.
- **Contract:** OpenAPI 3.1 generated from the API and consumed by the mobile client.

## Where am I?

- Workspace root: this folder.
- Canonical product source (read-only): [docs/VulnMNO.md](docs/VulnMNO.md). Methodology reference: [docs/MWP.md](docs/MWP.md).
- Stages live under `stages/`, numbered in execution order.
- Stable configuration lives under `_config/`; shared reference under `shared/`.
- Each stage owns `references/` (Layer 3) and `output/` (Layer 4 — includes generated code where applicable).

## Where do I go next?

Read [CONTEXT.md](CONTEXT.md) for workspace-level routing — it tells you which stage handles which question.

## Operating rules

1. **One stage at a time.** Read the stage's own `CONTEXT.md` before doing anything. Load only the files its `## Inputs` section lists.
2. **Never modify `docs/`.** It is the canonical product source. Derived knowledge (specs, code, fixtures) belongs in stage `output/`.
3. **The API contract is the seam.** Stage 02's OpenAPI spec is the single source of truth shared by backend (stages 03–04) and mobile (stages 05–06). When the contract changes, stage 02 changes first, then downstream stages regenerate.
4. **Layer 3 vs Layer 4.** Files in `_config/`, `shared/`, and `stages/*/references/` are *constraints to internalize* (style, conventions, scaffolding rules). Files in `stages/*/output/` are *artifacts produced by this run* (specs, code, fixtures).
5. **Code lives in stage outputs.** The backend project lives at `stages/04_api_build/output/backend/`. The Android project lives at `stages/06_mobile_build/output/android/`. Stage 07 wires them together.
6. **No framework orchestration.** Folder structure is the orchestration. If a stage seems to require branching, ask the human.

## Scope reminder

VulnMNO is a synthetic, training-oriented product. Phase 1 builds the functional surface. Threats, fraud and controls reviews are explicitly *out of scope* for this workspace — they would be a separate analytical workspace consuming the artifacts produced here.
