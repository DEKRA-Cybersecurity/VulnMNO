# VulnMNO — phases 1 + 2

A fictional Mobile Network Operator platform built end-to-end (backend API + Android app + admin web portal) for training purposes. Product description: [docs/VulnMNO.md](docs/VulnMNO.md). Methodology (folder-structure-as-architecture): [docs/MWP.md](docs/MWP.md).

> **Scope.** Phase 1 implements the six customer journeys from VulnMNO §9 (login, purchase, plan change, usage, invoice, support) via a JWT-based mobile API. Phase 2 adds a server-rendered admin portal (Jinja2 + HTMX + Bootstrap), external integration adapters (payment gateway / provisioning / FCM push), loyalty engine, agent ticket replies, refund approval workflow, rate limiting, and i18n.

## Workspace layout

```
VulnMNO/
├── docs/                          # canonical product source — never modified
├── _config/                       # factory config (conventions, tech stack, code style)
├── shared/                        # glossary, source-pointer
├── setup/                         # per-run questionnaire
└── stages/
    ├── 01_requirements/           # phase 1 backlog + traceability
    ├── 02_api_contract/           # OpenAPI 3.1 + auth model + error codes
    ├── 03_data_model/             # SQLAlchemy models + Alembic 0001 + seed
    ├── 04_api_build/              # FastAPI backend (runnable, phase 1 + phase 2 in-place)
    ├── 05_mobile_design/          # phase 1 screens + navigation + state model
    ├── 06_mobile_build/           # Android app (Kotlin + Compose) — phase 1 + i18n
    ├── 07_integration/            # phase 1 E2E + docker-compose + this README seed
    ├── 08_phase2_requirements/    # phase 2 backlog + RBAC matrix
    ├── 09_phase2_contract/        # extended OpenAPI + adapter Protocol interfaces
    ├── 10_phase2_data_model/      # admin_users + loyalty_* + Alembic 0002 + seed_phase2
    ├── 11_admin_portal_build/     # admin/ subpackage + Jinja2 templates + Bootstrap static
    ├── 12_integrations_and_ops/   # gateway adapters + slowapi + i18n + loyalty + campaigns
    └── 13_phase2_integration/     # phase 2 smoke + docker-compose + run-log
```

Each stage owns a `CONTEXT.md` (its contract) and an `output/` (its artifacts). Code lives inside the relevant stage's `output/`. Never modify `docs/`.

## Prerequisites

- **Backend:** Python 3.12+, `pip` (or `uv`), SQLite for dev.
- **Mobile:** Android Studio Hedgehog or newer, Android SDK 34, an emulator (Pixel 6 / API 34 recommended), Gradle 8.10.2.
- **Optional prod-like profile:** Docker + Docker Compose.

## Quick start — backend (dev, SQLite)

```bash
cd stages/04_api_build/output/backend
pip install -U \
  "fastapi>=0.110" "uvicorn[standard]>=0.27" \
  "sqlalchemy>=2.0" "alembic>=1.13" "aiosqlite>=0.19" "asyncpg>=0.29" \
  "pydantic>=2.6" "pydantic-settings>=2.2" \
  "PyJWT>=2.8" "argon2-cffi>=23" "python-multipart>=0.0.9" \
  "jinja2>=3.1" "itsdangerous>=2.2" "httpx>=0.27" "slowapi>=0.1.9" "PyYAML>=6.0"

uvicorn app.main:app --reload --port 8000
```

The first request triggers the lifespan handler, which creates the schema, runs `app.seed` (Phase 1 customers), then `app.seed_phase2` (admin staff + loyalty tiers). All seeds are idempotent.

Run the test suite (43 cases — 24 phase 1 + 19 phase 2 admin) with:

```bash
python -m pytest -q
```

## Quick start — admin portal (phase 2)

With the backend running, open `http://localhost:8000/admin/login` in any browser. Seeded admin staff (password `admin1234` for all):

| Username | Role | Can do |
| --- | --- | --- |
| `support` | support_agent | Customer search, ticket triage + agent replies |
| `billing` | billing_operator | Balance adjustments, refund approve/reject, audit read |
| `product` | product_manager | Plan / promotion / coupon CRUD |
| `ops` | ops_admin | Everything (incl. admin user management) |
| `security` | security_analyst | Audit log + reports (read-only) |

The admin portal is server-rendered (Jinja2 + HTMX + Bootstrap from CDN). Every mutating action requires a CSRF token (auto-injected by the templates) and writes an `AuditEvent ADMIN_*` row. Role-based access is enforced by the RBAC matrix in [stages/08_phase2_requirements/output/admin-rbac-matrix.md](stages/08_phase2_requirements/output/admin-rbac-matrix.md).

## Quick start — Android (debug build)

```bash
cd stages/06_mobile_build/output/android
gradle wrapper --gradle-version 8.10.2     # one-off; Android Studio does this on first sync
./gradlew :app:installDebug                # requires a running emulator or device
```

The app uses `BuildConfig.BASE_URL = http://10.0.2.2:8000` in `debug`, which maps to the host's loopback for emulators. For a physical device, override `BASE_URL_DEBUG` in `gradle.properties` with the LAN IP of the machine running uvicorn.

Seeded test customers:

| MSISDN | Password | OTP | Notes |
| --- | --- | --- | --- |
| `+34600000001` | `secret123` | no | Alice — prepaid, balance €25.50, PREPAID-PLUS |
| `+34600000002` | `secret123` | yes (`123456`) | Bruno — postpaid, balance €0.00, UNLIMITED-PREMIUM, owns `INV-20001` |
| `+34600000003` | `secret123` | no | Clara — hybrid, balance €12.00, STUDENT-25 |

## End-to-end smoke

Two scripts cover the two surfaces, both headless against a running backend.

**Phase 1 — customer JSON API** (10 cases, the six §9 journeys + auth edge cases):

```bash
bash stages/07_integration/output/scripts/smoke_api.sh
```

**Phase 2 — admin portal + loyalty + i18n + rate limit** (8 cases):

```bash
bash stages/13_phase2_integration/output/scripts/smoke_admin.sh
```

Both exit non-zero on first failure. Last recorded runs:
[Phase 1 run-log](stages/07_integration/output/run-log.md) ·
[Phase 2 run-log](stages/13_phase2_integration/output/run-log.md).

For the UI pass on Android, follow:
- Phase 1: [stages/07_integration/output/scripts/smoke_mobile.md](stages/07_integration/output/scripts/smoke_mobile.md)
- Phase 2 extension (loyalty + i18n + refund cross-flow): [stages/13_phase2_integration/output/scripts/smoke_mobile.md](stages/13_phase2_integration/output/scripts/smoke_mobile.md)

## Gateway driver matrix (Phase 2)

Three integrations are pluggable per env. Default = `dev` (in-process, no external calls — Phase 1 behavior preserved).

| Integration | Env switch | Real driver | When to use |
| --- | --- | --- | --- |
| Payment | `VULNMNO_PAYMENT_DRIVER=stripe` + `VULNMNO_STRIPE_SECRET_KEY=...` | `StripePaymentGateway` (httpx → Stripe sandbox) | Verify charge/refund + idempotency-key forwarding |
| Provisioning | `VULNMNO_PROVISIONING_DRIVER=http` + `VULNMNO_PROVISIONING_URL=...` | `HttpProvisioning` (POST to mock service) | Exercise async retries + `PROVISIONING_FAILED` |
| Push delivery | `VULNMNO_PUSH_DRIVER=fcm` + `VULNMNO_FCM_CREDENTIALS_PATH=...` | `FcmPush` (firebase-admin SDK) | Verify delivery_status + provider_message_id |

Full settings reference: [stages/12_integrations_and_ops/output/settings-delta.md](stages/12_integrations_and_ops/output/settings-delta.md).

## Prod-like profile (PostgreSQL + provisioning mock via Docker)

Phase 2 extends the Phase-1 compose with a tiny `provisioning-mock` service:

```bash
docker compose -f stages/13_phase2_integration/output/docker-compose.yml up --build
```

Brings up:

- `db` — PostgreSQL 16 on `localhost:5432`.
- `provisioning-mock` — minimal FastAPI service on `localhost:9000` answering `POST /activate`.
- `backend` — the FastAPI app on `localhost:8000`, connected via `postgresql+asyncpg://`, with `VULNMNO_PROVISIONING_DRIVER=http` wired to the mock.

To swap in Stripe sandbox or FCM, edit the `backend` env block.

The Android emulator continues to point at `10.0.2.2:8000`. Seeding still runs on startup.

## Where to look when something breaks

| Symptom | Look at |
| --- | --- |
| Wrong endpoint shape | [stages/02_api_contract/output/openapi.yaml](stages/02_api_contract/output/openapi.yaml) (contract) vs [stages/04_api_build/output/openapi.generated.yaml](stages/04_api_build/output/openapi.generated.yaml) (served) — diff via [contract-deltas.md](stages/04_api_build/output/contract-deltas.md). |
| Auth flow weirdness | [stages/02_api_contract/output/auth-model.md](stages/02_api_contract/output/auth-model.md). |
| DB schema or seed issue | [stages/03_data_model/output/entities.md](stages/03_data_model/output/entities.md), [seed.py](stages/04_api_build/output/backend/app/seed.py). |
| Domain error in app | Backend error envelope codes in [stages/02_api_contract/output/error-codes.md](stages/02_api_contract/output/error-codes.md); app mapping in [ApiResult.kt](stages/06_mobile_build/output/android/app/src/main/java/com/vulnmno/app/data/remote/ApiResult.kt). |
| Screen missing or behaves oddly | [stages/05_mobile_design/output/screens.md](stages/05_mobile_design/output/screens.md), [navigation.md](stages/05_mobile_design/output/navigation.md), [state-model.md](stages/05_mobile_design/output/state-model.md); build mapping in [stages/06_mobile_build/output/screens-built.md](stages/06_mobile_build/output/screens-built.md). |

## Methodology one-pager

This workspace follows the **Model Workspace Protocol (MWP)** described in [docs/MWP.md](docs/MWP.md): one agent reads different markdown contracts at each stage; folder structure replaces framework orchestration. Each stage's `CONTEXT.md` defines its inputs, process, and outputs. Editing a stage's reference material (`stages/*/references/`, `_config/`, `shared/`) changes what every future run does; editing `stages/*/output/` only changes the current run.

## Phase 3 (not in this workspace)

VulnMNO §13 ships explicit operational assumptions (Apache Log4j 2.14 on the analytics service, multi-day sessions, SMS-based reset, etc.). A separate analytical workspace can consume these artifacts to produce a threat model, fraud scenarios, and controls review without touching this build. That work is intentionally out of scope here.

Functional follow-ups deferred to Phase 3 (documented as `OUT-OF-PHASE-2` in [stages/08_phase2_requirements/output/backlog.md](stages/08_phase2_requirements/output/backlog.md)):

- Loyalty points **redemption** (discount purchases with accrued points).
- **Multi-factor auth** for admin staff (especially `ops_admin`).
- **Supplier portal** with per-supplier scope isolation (the `supplier_admin` role exists but has zero permissions in Phase 2).
- **Push notification inbox** on the mobile app (delivery_status is recorded but the in-app inbox surface isn't built).
- **Real FCM credentials** in CI; Stage 13 docker-compose runs `dev` push by default.
