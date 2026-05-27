# Code style

## Python (backend)

### Project layout (under `stages/04_api_build/output/backend/`)

```
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/
├── app/
│   ├── main.py            # FastAPI app factory, router includes, OpenAPI export
│   ├── config.py          # Pydantic Settings
│   ├── db.py              # async engine + session
│   ├── deps.py            # FastAPI dependencies (current_user, db session)
│   ├── security.py        # JWT, password hashing, OTP
│   ├── models/            # SQLAlchemy ORM models, one file per aggregate
│   ├── schemas/           # Pydantic v2 schemas, one file per resource
│   ├── routers/           # one file per §12 endpoint group
│   ├── services/          # business logic (purchase, promotion, plan-change…)
│   └── seed.py            # idempotent seed loader
├── tests/
│   ├── conftest.py
│   └── test_<router>.py
└── README.md
```

### Style

- Format and lint with `ruff` and `ruff format`. Line length 100.
- All public functions have type hints; mypy strict on `app/`.
- Prefer `async def` end-to-end in `app/`. Synchronous helpers go in `app/utils/` and are clearly named.
- No global state outside `db.py` and `config.py`. Everything else is injected via FastAPI `Depends`.
- Routers contain orchestration only. Business rules live in `app/services/`.
- Money is `Decimal` in models and services, serialized as JSON number with two decimal places to match `docs/VulnMNO.md` §13 examples.
- Datetimes are timezone-aware UTC, serialized as `2026-05-26T10:30:00Z`.

### Errors

Single error envelope:

```json
{ "error": { "code": "PROMO_INELIGIBLE", "message": "…", "details": {} } }
```

`code` is a `SCREAMING_SNAKE` enum defined alongside the router that raises it. Stage 02 maintains the master list in the OpenAPI spec.

## Kotlin (Android)

### Project layout (under `stages/06_mobile_build/output/android/`)

```
android/
├── settings.gradle.kts
├── build.gradle.kts                  # Kotlin DSL, version catalog
├── gradle/libs.versions.toml
└── app/
    ├── build.gradle.kts
    └── src/main/
        ├── AndroidManifest.xml
        └── java/com/vulnmno/app/
            ├── VulnMnoApp.kt          # @HiltAndroidApp
            ├── MainActivity.kt        # single activity, hosts NavHost
            ├── ui/
            │   ├── theme/             # Material 3 theme
            │   ├── navigation/        # NavGraph, routes
            │   └── screens/           # one package per SCR-
            ├── data/
            │   ├── remote/
            │   │   ├── ApiService.kt  # Retrofit interface
            │   │   ├── dto/           # generated DTOs (XxxDto)
            │   │   └── AuthInterceptor.kt
            │   ├── local/             # DataStore for tokens
            │   └── repository/        # one repo per resource
            ├── domain/
            │   ├── model/             # UI-facing models
            │   └── usecase/           # one use case per user action
            └── di/                    # Hilt modules
```

### Style

- Format with `ktlint`. No wildcard imports.
- One Composable per file when it owns its own state; multiple Composables per file allowed only for tightly coupled subtrees.
- ViewModels expose `StateFlow<UiState>` — no `LiveData`.
- `UiState` is a sealed interface with `Loading`, `Content(data)`, `Error(message)`.
- All side effects go through use cases (`domain/usecase/`). Composables never call repositories directly.
- Networking errors map to a `Result` sealed type at the repository boundary. UI never sees raw `HttpException`.

### DTO ↔ domain mapping

DTOs (`XxxDto`) are wire shapes. Domain models live in `domain/model/`. Mapping happens in repositories — never in ViewModels or Composables.

### Theming

Material 3 with dynamic color enabled. Brand palette can be defined later; for phase 1 use the Material 3 baseline.
