# Stage 06 — Mobile build (Android, Kotlin, Compose)

Implement the Android app so that every `SCR-…` from stage 05 is functional against the backend produced by stage 04.

## Inputs

**Layer 4 (working):**
- `../02_api_contract/output/openapi.yaml` — wire-shape source of truth for DTOs.
- `../02_api_contract/output/endpoints.md`
- `../02_api_contract/output/error-codes.md`
- `../05_mobile_design/output/screens.md`
- `../05_mobile_design/output/navigation.md`
- `../05_mobile_design/output/state-model.md`

**Layer 3 (reference):**
- `references/implementation-checklist.md` — screen build order and per-screen DoD.
- `../../_config/code-style.md` — Android project layout, naming, package structure.
- `../../_config/tech-stack.md` — Compose, Retrofit, Hilt, version catalog.
- `../../_config/conventions.md` — DTO naming, error envelope.

## Process

1. Scaffold the Android project at `output/android/` per `_config/code-style.md` (single-activity Compose app, Hilt, version catalog, Material 3).
2. Generate or hand-write DTOs in `data/remote/dto/` matching `openapi.yaml`. If hand-writing, validate by deserializing the example payloads from `docs/VulnMNO.md` §13 (snapshot tests in `app/src/test/`).
3. Set up Retrofit + Kotlinx Serialization + an `AuthInterceptor` that adds the bearer token and a `TokenAuthenticator` that triggers refresh on `401`.
4. Implement screens in the order defined in `references/implementation-checklist.md`. Each screen:
   - ViewModel with `StateFlow<UiState>` matching `state-model.md`.
   - Repository + use cases per `code-style.md`.
   - Composable screen file under `ui/screens/<package>/`.
   - At least one UI test (Compose UI Test) covering the happy path.
5. Wire navigation per `navigation.md`: one `NavHost`, typed routes, deep links for `vulnmno://shop`, `vulnmno://invoices/{id}`.
6. Implement the global `401` listener: drop tokens, navigate to `LoginScreen`, preserve the intended destination in saved state.
7. Build variants: `debug` points at `http://10.0.2.2:8000`; `release` reads `BASE_URL` from `gradle.properties`.

## Outputs

Under `output/`:

- `android/` — full Android Studio project, opens in Android Studio Hedgehog or later, builds with `./gradlew :app:assembleDebug`.
- `coverage-summary.md` — JaCoCo or built-in Compose coverage report summary for ViewModels and repositories.
- `screens-built.md` — checklist mapping every `SCR-…` from stage 05 to the file(s) implementing it.

## Definition of done for this stage

- `./gradlew :app:assembleDebug` succeeds.
- App boots in the emulator (Pixel 6, API 34) and reaches `LoginScreen`.
- Logging in as a seeded customer reaches `HomeScreen` with balance, current plan and one promo card populated from the API.
- Every `SCR-…` in `screens.md` has a corresponding row in `screens-built.md` and at least one passing UI test.
- No usage of `LiveData`, no wildcard imports, ktlint clean.
