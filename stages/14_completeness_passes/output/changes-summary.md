# Stage 14 — completeness passes (summary)

Closed the four functional gaps between `docs/VulnMNO.md` and the build after
Phase 2.

## Backend changes (`stages/04_api_build/output/backend/`)

### Gap 1 — SIM swap workflow

- `app/schemas/customer.py`: added `SimSwapRequest`, `SimSwapResult`.
- `app/routers/customers.py`: new endpoint
  `POST /api/customers/me/sim-swap` (body `{newSimType, reason?}`). Marks the
  current `SIMProfile.status = "swapped"`, creates a fresh SIM (ICCID +
  IMSI alias), links it to the line and writes an audit
  event `SIM_SWAP_REQUEST` carrying `oldSimId`, `newSimType`, `reason` and the
  caller IP — matches the §12.4 SIM_SWAP_REQUEST example.
- `app/ids.py`: added `next_sim_id()` (`SIM-8xxxx` range).

### Gap 2 — Device registry

- New model `app/models/device.py::CustomerDevice` with
  `(customer_id, device_id)` unique, `platform`, `model`, `app_version`,
  `first_seen_at`, `last_seen_at`, `trusted`.
- `app/schemas/auth.py`: `DeviceRegisterRequest`, `DeviceRegisterResult`.
- `app/routers/auth.py`:
  - New endpoint `POST /api/auth/devices` (auth required). First call returns
    `recognized=false`; subsequent calls return `recognized=true` and update
    `last_seen_at`/`app_version`.
  - Existing `POST /api/auth/login` now reads the optional `X-Device-Id`
    header and stores it in the `LOGIN_SUCCESS` audit payload, matching the
    `deviceId` field in the §12.1 example.
- Audit emits `DEVICE_REGISTERED` (first time) or `DEVICE_SEEN`
  (subsequent), with target_type=`device`.
- `app/models/customer.py`: `Customer.devices` relationship.

### Migration

- `alembic/versions/2026_05_27_0003_completeness.py` creates `customer_devices`
  table and enum `customer_device_platform`.

### Tests

- `tests/test_completeness.py` (6 cases): device first-time + recognized,
  unauth, login with `X-Device-Id`, SIM swap (Bruno fixture to avoid
  alphabetical-order collision with `test_customers.py`).

## Mobile changes (`stages/06_mobile_build/output/android/`)

### DTOs / API client

- `Dtos.kt`: `SimSwapRequestDto`, `SimSwapResultDto`,
  `DeviceRegisterRequestDto`, `DeviceRegisterResultDto`.
- `ApiService.kt`: `simSwap()`, `registerDevice()` endpoints.
- `Repositories.kt::SupportRepository.addAttachment()` wraps the existing
  multipart endpoint.

### Gap 3 — Usage export UI

- `ui/screens/usage/UsageScreen.kt` rewritten: top app bar with a download
  icon. `UsageViewModel.exportCsv()` calls the existing `/api/usage/export?format=csv`,
  writes bytes to `cacheDir`, exposes a FileProvider URI and the screen fires
  `Intent.ACTION_VIEW` (chooser) with `text/csv`.

### Gap 4 — Ticket attachments UI

- `ui/screens/support/SupportScreens.kt`:
  - `TicketDetailViewModel.upload()` uses `ContentResolver` to read the picked
    `Uri`, detects filename + mime, calls `SupportRepository.addAttachment()`.
  - `TicketDetailScreen` gets a paperclip icon in the top app bar
    (`ActivityResultContracts.GetContent`), a progress indicator while
    uploading, a flash banner after success, and a list of attachments
    rendered below the message stream.

## Verification

- `pytest -q`: 49 passed (was 43 before this stage).
- `./gradlew :app:compileDebugKotlin`: BUILD SUCCESSFUL.
- Manual TestClient smoke: login → register device twice (first
  `recognized=false`, second `recognized=true`) → SIM swap (`SIM-10002` →
  `swapped`, new `SIM-80004` esim active) → re-read SIM profile returns the
  new one.

## Out of scope (deferred)

- Trusted-device step-up auth challenges.
- Cloud storage for attachments (still local filesystem under
  `VULNMNO_UPLOADS_DIR`).
- Mobile UI for SIM swap and device registration — backend ready, exposing
  these in the app is a Phase 3 UX decision (e.g. inside Settings).
