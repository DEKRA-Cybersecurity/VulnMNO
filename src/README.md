# VulnMNO — product source tree

This `src/` folder holds the **consumable product**: backend API, admin portal
templates/assets, Android client, and Docker ops files — all in a normal
production/development layout. The `stages/` folder at the repo root is the
build-history workspace (MWP methodology) used to design new features; once
work there is validated, the latest outputs are copied here.

```
src/
├── backend/          FastAPI app + admin portal + Alembic migrations + tests
├── mobile/
│   └── android/      Kotlin + Jetpack Compose client (minSdk 26)
├── docker/           Dockerfile + docker-compose.yml (prod-like stack)
├── scripts/          smoke_api.sh, smoke_admin.sh
└── README.md         (this file)
```

## What's in here

- **Phase 1 customer API** — 42 endpoints covering login, balance, shop,
  plans, usage, invoices, support, notifications (docs §9 + §12).
- **Phase 2 admin portal** — server-rendered Jinja2 + HTMX + Bootstrap 5
  with a dark-sidebar dashboard. Six RBAC roles. Mount at `/admin/`.
- **Phase 2 integrations** — payment / provisioning / FCM gateway adapters
  (Protocol-based, swap drivers via env var), slowapi rate limiting, YAML
  i18n catalogs (en + es), loyalty engine, refund approval, campaign
  scheduler.
- **Stage 14 completeness** — SIM swap workflow, device registry, usage
  CSV export, ticket attachments upload UI.

---

## Backend — local dev (SQLite)

```bash
cd src/backend
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload
```

- API & OpenAPI: `http://localhost:8000/docs`
- Admin portal:  `http://localhost:8000/admin/`
  (seeded login: **ops / admin1234** — also `support`, `billing`, `product`,
  `security` with the same password)
- Customer login (seeded): MSISDN `+34600000001` / password `secret123`

```bash
pytest -q          # 49 tests
```

## Docker — prod-like stack (PostgreSQL + provisioning mock)

```bash
cd src
docker compose -f docker/docker-compose.yml up --build
```

Flip these env vars in `docker/docker-compose.yml` to exercise real gateways:

| Var | Default | Real |
|---|---|---|
| `VULNMNO_PAYMENT_DRIVER`      | `dev`  | `stripe` (set `VULNMNO_STRIPE_SECRET_KEY=sk_test_…`) |
| `VULNMNO_PROVISIONING_DRIVER` | `http` (points at mock) | `http` (point at real URL) |
| `VULNMNO_PUSH_DRIVER`         | `dev`  | `fcm` (set `VULNMNO_FCM_CREDENTIALS_PATH=…`) |
| `VULNMNO_DEFAULT_LOCALE`      | `en`   | `es` |
| `VULNMNO_RATE_LIMIT_ENABLED`  | `true` | `false` |

## Smoke checks

After the backend is up:

```bash
BASE_URL=http://localhost:8000 scripts/smoke_api.sh    # Phase 1 customer journeys
BASE_URL=http://localhost:8000 scripts/smoke_admin.sh  # Phase 2 admin + loyalty + i18n
```

---

## Mobile (Android)

Open `src/mobile/android` in Android Studio (Iguana+) or build from CLI:

```bash
cd src/mobile/android
./gradlew :app:assembleDebug
./gradlew :app:installDebug         # connected device / emulator
```

By default the app points at `http://10.0.2.2:8000` (emulator → host loopback).
Override in `app/build.gradle.kts` if running on a physical device.

Seeded login:

| MSISDN | Password | Notes |
|---|---|---|
| `+34600000001` | `secret123` | password-only flow |
| `+34600000002` | `secret123` | OTP challenge — code `123456` |
| `+34600000003` | `secret123` | password-only flow |

---

## Relationship to `stages/`

- `stages/` (sibling of `src/`) holds the **design history**: requirements,
  contracts, plans, references, output artefacts of each MWP stage.
- `src/` holds the **shipping artefacts** — code you can run.
- When `stages/` produces a new validated build, sync it forward:

```bash
# from repo root
rsync -a --delete \
  --exclude '__pycache__/' --exclude '*.pyc' --exclude 'dev.db' --exclude 'uploads/' \
  stages/04_api_build/output/backend/ src/backend/

rsync -a --delete \
  --exclude '.gradle/' --exclude 'build/' --exclude '.idea/' --exclude 'local.properties' \
  stages/06_mobile_build/output/android/ src/mobile/android/
```

Tests gate the sync: backend `pytest -q` (49 passing) and Android
`./gradlew :app:compileDebugKotlin` (BUILD SUCCESSFUL) must both stay green.
