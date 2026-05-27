# VulnMNO — Quickstart

This guide explains how to run the **backend** (FastAPI + admin portal) and the
**Android client** that together make up the VulnMNO platform.

All source ships under `src/`:

```
src/
├── backend/          FastAPI app + admin portal + tests
├── mobile/android/   Kotlin + Jetpack Compose client
├── docker/           Dockerfile + docker-compose.yml
└── scripts/          smoke_api.sh, smoke_admin.sh
```

---

## 1. Backend — cloud-style with `docker compose`

The compose stack brings up three services: **PostgreSQL 16**, a tiny
**provisioning mock** (FastAPI stub), and the **backend** itself. The backend
seeds itself on first boot (customers, plans, products, admin users), so the
stack is usable immediately after the build.

```bash
cd src
docker compose -f docker/docker-compose.yml up --build
```

Once the logs report `Uvicorn running on http://0.0.0.0:8000`:

| Surface         | URL                                  | Notes                                                 |
| --------------- | ------------------------------------ | ----------------------------------------------------- |
| OpenAPI / Swagger | <http://localhost:8000/docs>       | All customer-facing endpoints                         |
| Admin portal    | <http://localhost:8000/admin/>       | Login `ops` / `admin1234` (also `support`, `billing`, `product`, `security` — same password) |
| Customer API    | <http://localhost:8000/api/…>        | JWT-bearer auth — see endpoint table below            |
| PostgreSQL      | `localhost:5432` (`vulnmno:vulnmno`) | Phase-2 prod-like DB                                  |

Seeded customer credentials for testing the API directly or from the mobile
client:

| MSISDN          | Password    | Notes                              |
| --------------- | ----------- | ---------------------------------- |
| `+34600000001`  | `secret123` | Password-only login                |
| `+34600000002`  | `secret123` | OTP challenge — fixed code `123456` |
| `+34600000003`  | `secret123` | Password-only login                |

Stop the stack with `Ctrl-C` (or `docker compose -f docker/docker-compose.yml down -v` to also drop the volumes).

### Switching gateway drivers

The compose file ships every external integration on its `dev` driver so the
stack runs offline. Flip these env vars to point at real services:

```yaml
VULNMNO_PAYMENT_DRIVER: stripe         # + VULNMNO_STRIPE_SECRET_KEY=sk_test_…
VULNMNO_PUSH_DRIVER:    fcm            # + VULNMNO_FCM_CREDENTIALS_PATH=/run/secrets/fcm.json
VULNMNO_PROVISIONING_DRIVER: http      # already on; flip URL to a real provisioning system
VULNMNO_DEFAULT_LOCALE: es             # API error messages in Spanish
```

### Smoke checks

With the stack running:

```bash
BASE_URL=http://localhost:8000 src/scripts/smoke_api.sh    # Phase 1 customer journeys
BASE_URL=http://localhost:8000 src/scripts/smoke_admin.sh  # Phase 2 admin + loyalty + i18n
```

---

## 2. Backend — local dev (SQLite, no Docker)

For tight iteration loops:

```bash
cd src/backend
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload
```

Tests (49 cases):

```bash
pytest -q
```

---

## 3. API endpoint summary

Every route is prefixed with `/api`. Authentication uses `Authorization: Bearer
<accessToken>` (obtained from `POST /api/auth/login`) unless noted.

| Group         | Method | Path                                            | Purpose                              |
| ------------- | ------ | ----------------------------------------------- | ------------------------------------ |
| **Auth**      | POST   | `/api/auth/login`                               | Login (password ± OTP challenge)     |
|               | POST   | `/api/auth/otp/verify`                          | Exchange OTP challenge for tokens    |
|               | POST   | `/api/auth/refresh`                             | Refresh access token                 |
|               | POST   | `/api/auth/logout`                              | Revoke refresh token                 |
|               | POST   | `/api/auth/password-reset/request`              | Start password reset                 |
|               | POST   | `/api/auth/password-reset/confirm`              | Complete password reset              |
|               | POST   | `/api/auth/devices`                             | Register a logical device id        |
| **Customers** | GET    | `/api/customers/me`                             | Customer profile                     |
|               | PUT    | `/api/customers/me/contact-details`             | Update email / address / prefs       |
|               | GET    | `/api/customers/me/lines`                       | List mobile lines                    |
|               | GET    | `/api/customers/me/sim-profile`                 | Current SIM/eSIM                     |
|               | POST   | `/api/customers/me/sim-swap`                    | Swap SIM, mark old as `swapped`      |
| **Accounts**  | GET    | `/api/accounts/me/balance`                      | Wallet balance                       |
|               | GET    | `/api/accounts/me/transactions`                 | Transaction history                  |
|               | POST   | `/api/accounts/me/topup`                        | Wallet top-up                        |
|               | GET    | `/api/accounts/me/invoices`                     | Invoice list                         |
|               | GET    | `/api/accounts/me/invoices/{invoiceId}`         | Invoice detail                       |
|               | GET    | `/api/accounts/me/invoices/{invoiceId}/download`| Invoice PDF                          |
|               | POST   | `/api/accounts/me/refunds`                      | Open refund request                  |
| **Shop**      | GET    | `/api/shop/products`                            | Catalog                              |
|               | GET    | `/api/shop/products/{productId}`                | Product detail                       |
|               | POST   | `/api/shop/promotions/apply`                    | Validate promo / discount preview    |
|               | POST   | `/api/shop/purchases`                           | Create purchase                      |
|               | GET    | `/api/shop/purchases`                           | Purchase history                     |
|               | GET    | `/api/shop/purchases/{purchaseId}`              | Purchase detail                      |
|               | POST   | `/api/shop/purchases/{purchaseId}/cancel`       | Cancel a pending purchase            |
| **Plans**     | GET    | `/api/plans/current`                            | Active plan                          |
|               | GET    | `/api/plans/available`                          | Eligible plans                       |
|               | POST   | `/api/plans/change`                             | Schedule / apply plan change         |
|               | POST   | `/api/plans/change/{changeId}/cancel`           | Cancel scheduled change              |
|               | POST   | `/api/plans/services/add`                       | Activate optional service            |
|               | POST   | `/api/plans/services/remove`                    | Deactivate optional service          |
| **Usage**     | GET    | `/api/usage/calls`                              | Call records                         |
|               | GET    | `/api/usage/sms`                                | SMS records                          |
|               | GET    | `/api/usage/data`                               | Data sessions                        |
|               | GET    | `/api/usage/roaming`                            | Roaming records                      |
|               | GET    | `/api/usage/export?format=csv\|json`            | Export usage as CSV/JSON             |
| **Support**   | POST   | `/api/support/tickets`                          | Create ticket                        |
|               | GET    | `/api/support/tickets`                          | List own tickets                     |
|               | GET    | `/api/support/tickets/{ticketId}`               | Ticket detail (with messages)        |
|               | POST   | `/api/support/tickets/{ticketId}/messages`      | Add customer message                 |
|               | POST   | `/api/support/tickets/{ticketId}/attachments`   | Upload attachment (multipart)        |
|               | POST   | `/api/support/tickets/{ticketId}/close`         | Close ticket                         |
| **Notifications** | GET   | `/api/notifications`                         | List in-app notifications            |
|               | POST   | `/api/notifications/preferences`                | Update channel preferences           |
|               | POST   | `/api/notifications/device-token`               | Register an FCM push token           |
| **Loyalty**   | GET    | `/api/loyalty/account`                          | Points balance + tier                |
|               | GET    | `/api/loyalty/transactions`                     | Points history                       |

The admin portal at `/admin/` is server-rendered (Jinja2 + HTMX) and is not
covered by the table above — explore it interactively after logging in.

---

## 4. Android client

### Features

The Compose app implements every customer journey listed in the product spec:

- **Auth** — phone + password login, OTP step-up, password reset, persistent
  session via DataStore + reactive `AuthGate`.
- **Home** — balance / current plan / recent usage summary, deep-link entry
  points to every section.
- **Account & Settings** — profile, SIM profile, contact details edit,
  per-channel notification toggles, language (read-only, follows device
  locale), sign-out.
- **Balance** — wallet balance, transaction history, top-up.
- **Shop** — product catalog, promo-code preview, purchase confirmation,
  purchase history.
- **Plans** — current plan, available plans, plan-change workflow,
  add/remove optional services.
- **Usage** — calls / SMS / data / roaming tabs, **CSV export** via system
  share sheet (uses `FileProvider`).
- **Invoices** — list + detail + PDF download (opens via `FileProvider`).
- **Support** — ticket list, new ticket form, ticket detail with agent
  thread, **file attachment upload**, close ticket.
- **Notifications** — in-app message list, FCM device-token registration on
  startup.
- **Loyalty** — points balance + tier card on the Account screen.

Tech stack: minSdk 26 / targetSdk 34, Kotlin, Jetpack Compose, Hilt for DI,
Retrofit + Kotlinx Serialization, OkHttp interceptors for bearer auth + token
refresh.

### 4.1 Run on a physical device

1. Enable **Developer options** → **USB debugging** on the device.
2. Plug it in and authorize the debugger fingerprint.
3. Make the backend reachable from the device. If the phone is on the same
   Wi-Fi as your laptop, find the laptop's LAN IP (`ip a` / `ifconfig`) and
   override the base URL at install time:

   ```bash
   cd src/mobile/android
   ./gradlew installDebug -PBASE_URL_DEBUG=http://192.168.1.42:8000
   ```

   (Replace the IP with yours. The backend must be listening on `0.0.0.0`, not
   `127.0.0.1` — `uvicorn --host 0.0.0.0` or the Docker stack already does
   this.)
4. Launch the app. Sign in with one of the seeded customers above.

### 4.2 Run on an Android emulator (CLI: `sdkmanager` + `avdmanager`)

This recipe avoids Android Studio and uses only the command-line tools that
ship with the Android SDK.

**Prerequisites:** install the **command-line tools** package from
<https://developer.android.com/studio#command-tools> and add it to your
environment:

```bash
export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
```

#### Install the SDK pieces (one-time)

```bash
# Accept all licenses (interactive 'y' on each)
sdkmanager --licenses

# Platform-tools (adb), platform 34, an x86_64 system image, the emulator
sdkmanager \
  "platform-tools" \
  "platforms;android-34" \
  "system-images;android-34;google_apis;x86_64" \
  "emulator"
```

#### Create an AVD

```bash
echo "no" | avdmanager create avd \
  --name vulnmno_pixel \
  --package "system-images;android-34;google_apis;x86_64" \
  --device "pixel_6"

avdmanager list avd          # confirm "vulnmno_pixel" is listed
```

#### Boot it and install the app

```bash
# Headless-ish: terminal stays attached and prints logs; -no-snapshot is
# friendlier on first boot.
emulator -avd vulnmno_pixel -no-snapshot &

# Wait until the device shows up
adb wait-for-device
adb shell 'while [[ -z $(getprop sys.boot_completed) ]]; do sleep 1; done'

# Build + install. http://10.0.2.2:8000 is the emulator's view of the host
# loopback (this is the default — no -PBASE_URL_DEBUG flag needed if the
# backend is on the same machine).
cd src/mobile/android
./gradlew installDebug

# Launch the activity
adb shell am start -n com.vulnmno.app/.MainActivity
```

Useful follow-ups:

```bash
adb logcat -s VulnMNO:V             # filter app logs
adb shell pm clear com.vulnmno.app  # wipe app state and re-login
emulator -avd vulnmno_pixel -wipe-data &   # cold-boot a clean image
```

To run the **release** variant against a remote backend:

```bash
./gradlew installRelease -PBASE_URL_RELEASE=https://api.example.test
```

---

## 5. Where to look when something breaks

| Symptom                                | Where to check                                                |
| -------------------------------------- | ------------------------------------------------------------- |
| Backend won't start                    | `docker compose … logs backend` or uvicorn stdout             |
| Migrations out of sync                 | `cd src/backend && alembic current && alembic upgrade head`   |
| Login returns 401                      | Verify seed ran (admin portal `/admin/` should also reject)   |
| Admin login returns 401                | Seeded creds are `ops / admin1234`, not the customer password |
| App stuck on splash                    | Backend unreachable from device — see §4.1 IP override        |
| `installDebug` fails: SDK not found    | `ANDROID_HOME` not set, or `local.properties` missing         |
| Tests failing locally                  | `cd src/backend && pytest -q`  must report 49 passed          |
