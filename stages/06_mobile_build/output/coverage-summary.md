# Coverage summary — stage 06

## Status

**No automated test run available in this stage.** The Android toolchain (Gradle, Android SDK, Kotlin compiler, JaCoCo) is not present in the workspace's CI image, so coverage could not be measured during the stage execution.

## What was verified

- **Static review.** Every `SCR-…` in [screens-built.md](screens-built.md) has a corresponding Kotlin file + ViewModel.
- **Wire-shape parity.** DTOs in [data/remote/dto/Dtos.kt](android/app/src/main/java/com/vulnmno/app/data/remote/dto/Dtos.kt) are derived from the stage-02 OpenAPI spec and the backend's served schema ([04_api_build/output/openapi.generated.yaml](../../04_api_build/output/openapi.generated.yaml)).
- **Compile-only dependencies declared.** The version catalog in [gradle/libs.versions.toml](android/gradle/libs.versions.toml) pins every dependency named in [`_config/tech-stack.md`](../../../_config/tech-stack.md).

## What stage 07 must verify

1. `./gradlew :app:assembleDebug` succeeds against the version catalog (run after the user adds the Gradle wrapper via `gradle wrapper --gradle-version 8.10.2`).
2. Emulator (Pixel 6, API 34) boots the app, reaches `LoginScreen`.
3. Logging in as `+34600000001 / secret123` (no-OTP customer) lands on `HomeScreen` with balance/plan/profile/featured-offers populated.
4. The §9.2 journey end-to-end (Shop → ProductDetail → Checkout → apply `SUMMER20` → buy `DATA-10GB-7D` → PurchaseConfirmation) leaves the wallet debited by €7.99.
5. The §9.6 journey (create ticket → message → close → message returns `TICKET_CLOSED`).

## Bootstrap checklist (for the user)

```bash
cd stages/06_mobile_build/output/android
# Generate the Gradle wrapper (one-off):
gradle wrapper --gradle-version 8.10.2

# Or open in Android Studio Hedgehog (or newer) which generates it on first sync.

# Backend (stage 04) must be running:
( cd ../../../04_api_build/output/backend && uvicorn app.main:app --reload --port 8000 ) &

# Build + install on a running emulator:
./gradlew :app:installDebug

# Run unit tests:
./gradlew :app:test
```

## Test surfaces planned (stage 07 wires the actual cases)

| Layer | What to cover | Tool |
| --- | --- | --- |
| ViewModels | Promo Apply/Invalid/Ineligible/Applied transitions, plan-ineligible rule, ticket-closed branch | JUnit4 + Turbine |
| Repositories | DTO ↔ wire-shape (snapshot deserialize §13 examples) | JUnit4 + MockWebServer |
| Composables | Compose UI test for LoginScreen, ShopScreen list, CheckoutScreen happy-path | Compose UI Test |
| Networking | `AuthInterceptor` adds bearer for protected paths, skips `/api/auth/*`. `TokenAuthenticator` triggers refresh on 401 then drops tokens on second 401. | MockWebServer |
