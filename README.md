# VulnMNO — phases 1 + 2 + lab hardening

A fictional Mobile Network Operator platform built end-to-end (backend API + Android client + admin web portal) for training. Now with TLS termination via Caddy, HTTPS-by-default mobile client, and deliberately seeded M1/M3 mobile vulnerabilities plus OWASP API Security Top 10 backend vulnerabilities for hacking labs. Product description: [docs/VulnMNO.md](docs/VulnMNO.md). Methodology: [docs/MWP.md](docs/MWP.md).

> **Scope.** Phase 1 implements the six §9 customer journeys via a JWT-based mobile API. Phase 2 adds a Jinja2 + HTMX admin portal, payment/provisioning/FCM adapters, loyalty engine, refund approval, rate limiting, and i18n. Stages 14–16 add SIM swap + device registry + attachments (completeness), Caddy TLS termination, and HTTPS-by-default in the Android client. Stage 17 seeds all ten OWASP API Security Top 10 categories into the backend. M1 / M3 mobile and API1–API10 backend vulnerabilities are intentional — see *Training-lab surface* below.

## Workspace layout

```
VulnMNO/
├── docs/                           # canonical product source — never modified
├── src/                            # shipping product (runnable)
│   ├── backend/                    # FastAPI + admin + Alembic
│   ├── mobile/android/             # Kotlin + Compose
│   ├── docker/                     # Dockerfile + docker-compose.yml + Caddyfile
│   ├── docs/vulns/mobile/          # M1 + M3 lab write-ups
│   ├── docs/vulns/api/             # API2/API4/API6/API8 lab write-ups
│   └── scripts/                    # smoke + Caddy CA install helpers
└── stages/                         # MWP build history (contracts + artefacts)
    ├── 01_requirements              · 02_api_contract     · 03_data_model
    ├── 04_api_build (backend)       · 05_mobile_design    · 06_mobile_build (android)
    ├── 07_integration               · 08_phase2_requirements
    ├── 09_phase2_contract           · 10_phase2_data_model
    ├── 11_admin_portal_build        · 12_integrations_and_ops
    ├── 13_phase2_integration        · 14_completeness_passes
    ├── 15_tls_termination           · 16_mobile_tls       · 17_api_security_lab
```

Each stage owns a `CONTEXT.md` (its contract), `references/` (constraints to internalize), and `output/` (artefacts of this run). Code lives in `src/` and is kept in sync with `stages/04/output/backend/` and `stages/06/output/android/` via `rsync` (excluding build artefacts). Never modify `docs/`.

## Quickstart

```bash
bash src/scripts/up.sh
```

Brings up Postgres, the backend (`:8000` plain HTTP for the API), the provisioning mock, and a Caddy reverse-proxy (`:443` HTTPS, terminates with a local CA). The script **auto-detects this host's LAN IP** (Linux-native, VPN-aware) and configures Caddy's cert for it, so HTTPS works on any network with zero edits — re-run it whenever you change networks. (`bash src/scripts/up.sh down` stops the stack.) On macOS / WSL2, or if detection guesses wrong, force it: `bash src/scripts/up.sh 192.168.1.50`.

Plain Compose still works (`cd src/docker && docker compose --profile tls up -d --build`) but only covers `localhost` + the emulator, and reuses any stale `docker/.env` from a prior `up.sh` run — prefer `up.sh`. Drop `--profile tls` to skip Caddy — backend still works but the admin portal won't accept login (its session cookie is `Secure`).

| URL | Use |
|---|---|
| `http://<host>:8000/api/*` | JSON API — Android client target |
| `http://<host>:8000/docs`  | OpenAPI / Swagger (unauth) |
| `https://<host>/admin/`    | Admin portal (browser only) |

Seed credentials:

- **Admin portal:** `ops` / `admin1234` (also `support`, `billing`, `product`, `security` — same password)
- **Customer API:** `+34600000001..03` / `secret123`
- **OTP login** (customer `…02`): `123456`
- **Password reset** (any customer): `123456`

Trust the Caddy local CA in your laptop / browser:

```bash
bash src/scripts/install_caddy_ca.sh        # writes ./caddy-root.crt + OS import hints
```

## Android client

```bash
cd src/mobile/android
./gradlew :app:installDebug                 # emulator or attached phone
```

Default base URL is `https://10.0.2.2/` (emulator → host loopback through Caddy). Before login on any device, push + install the Caddy root:

```bash
bash src/scripts/install_caddy_ca_android.sh
```

For a physical phone on the lab Wi-Fi, tap **Physical device?** on the login screen and type the host's LAN IP (the one `up.sh` printed as "Detected LAN IP"). Override truth table:

| Input | Effect |
|---|---|
| `<lan-ip>` (or `:443`)  | HTTPS via Caddy |
| `<lan-ip>:8000`         | Plain HTTP direct to backend — M1 L3 downgrade lab |
| `http://…` / `https://…`    | As typed |

No Caddyfile editing needed — `up.sh` already issued a cert for your LAN IP. Moved networks? Just re-run `bash src/scripts/up.sh`.

## Smoke checks

```bash
BASE_URL=http://localhost:8000 src/scripts/smoke_api.sh     # phase 1 customer journeys
BASE_URL=http://localhost:8000 src/scripts/smoke_admin.sh   # phase 2 admin + loyalty + i18n
```

Both exit non-zero on first failure. Recorded runs: [stages/07](stages/07_integration/output/run-log.md) · [stages/13](stages/13_phase2_integration/output/run-log.md).

## Database access

PostgreSQL 16 in `docker-db-1`, exposed on `localhost:5432`. Database / user / password all `vulnmno`.

```bash
docker exec -it docker-db-1 psql -U vulnmno -d vulnmno   # from the container, no password
PGPASSWORD=vulnmno psql -h localhost -U vulnmno -d vulnmno   # from the host
```

GUI clients (DBeaver, pgAdmin, TablePlus): host `localhost`, port `5432`, db / user / password all `vulnmno`.

Codes (`otp_challenges.code_hash`, `password_resets.code_hash`) are SHA-256 hashed — not recoverable from the DB. The fixed lab codes live in [src/backend/app/seed.py](src/backend/app/seed.py) (OTP login) and [src/backend/app/config.py](src/backend/app/config.py) (`password_reset_fixed_code`); the random fallback (when the fixed code is empty) is logged by the backend (`docker logs docker-backend-1 | grep -E 'OTP|PWRESET'`). No-Docker dev DB is SQLite at `src/backend/dev.db`. See [src/README.md](src/README.md) for starter queries.

## Training-lab surface

Deliberate, documented vulnerabilities under `src/docs/vulns/mobile/`:

- **M1 — Improper Credential Usage**
  - **L2.** Refresh + access tokens stored in plaintext DataStore (`/data/data/com.vulnmno.app/files/datastore/vulnmno_auth.preferences_pb`).
  - **L3.** Debug variant `network_security_config` permits cleartext + trusts user CAs; runtime downgrade via the `:8000` override or `-PBASE_URL_DEBUG=http://…` rebuild.
- **M3 — Insecure Authentication/Authorization**
  - **L1.** No rate-limit + no attempts cap on `/api/auth/otp/verify` → 6-digit code is brute-forceable inside the OTP TTL (asyncio PoC + auto-renewal of the challenge).
  - **L2.** Password-reset code is the fixed `123456` (per-customer override via `Customer.otp_fixed_code`, global default via `settings.password_reset_fixed_code`).
  - **L3.** Release variant trusts user-installed CAs (no cert pinning) — required for the Caddy local CA but leaves the door open to MITM via a malicious imported CA.

Each write-up has static-analysis hints, dynamic exploitation steps (mitmproxy / adb / curl / asyncio PoC), blue-team detection queries, and a remediation diff.

### API surface (OWASP API Security Top 10)

All ten 2023 categories are **live** — implemented and verified against a
running instance — under `src/docs/vulns/api/`, the backend-facing
counterpart to the M1/M3 mobile labs above. See
[stages/17_api_security_lab](stages/17_api_security_lab/) for the full
mapping and how each was verified.

- [API1 — Broken Object Level Authorization](src/docs/vulns/api/API1-Broken-Object-Level-Authorization.md)
- [API2 — Broken Authentication](src/docs/vulns/api/API2-Broken-Authentication.md)
- [API3 — Broken Object Property Level Authorization](src/docs/vulns/api/API3-Broken-Object-Property-Level-Authorization.md)
- [API4 — Unrestricted Resource Consumption](src/docs/vulns/api/API4-Unrestricted-Resource-Consumption.md)
- [API5 — Broken Function Level Authorization](src/docs/vulns/api/API5-Broken-Function-Level-Authorization.md)
- [API6 — Unrestricted Access to Sensitive Business Flows](src/docs/vulns/api/API6-Unrestricted-Access-to-Sensitive-Business-Flows.md)
- [API7 — Server Side Request Forgery](src/docs/vulns/api/API7-Server-Side-Request-Forgery.md)
- [API8 — Security Misconfiguration](src/docs/vulns/api/API8-Security-Misconfiguration.md)
- [API9 — Improper Inventory Management](src/docs/vulns/api/API9-Improper-Inventory-Management.md)
- [API10 — Unsafe Consumption of APIs](src/docs/vulns/api/API10-Unsafe-Consumption-of-APIs.md)

## Gateway driver matrix (Phase 2)

Pluggable via env vars; defaults to `dev` (in-process mocks — offline-friendly).

| Integration | Env switch | Real driver |
|---|---|---|
| Payment | `VULNMNO_PAYMENT_DRIVER=stripe` + `…_STRIPE_SECRET_KEY=…` | Stripe sandbox via httpx |
| Provisioning | `VULNMNO_PROVISIONING_DRIVER=http` + `…_PROVISIONING_URL=…` | HTTP POST to any service |
| Push | `VULNMNO_PUSH_DRIVER=fcm` + `…_FCM_CREDENTIALS_PATH=…` | Firebase Admin SDK |

Full reference: [stages/12_integrations_and_ops/output/settings-delta.md](stages/12_integrations_and_ops/output/settings-delta.md).

## Backend without Docker (SQLite dev)

```bash
cd src/backend
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload
```

Set `VULNMNO_ENV=dev` to drop the `Secure` cookie flag so the admin portal works over plain HTTP. Test suite: `python -m pytest -q`.

## Where to look when something breaks

| Symptom | Look at |
|---|---|
| Wrong endpoint shape | [02_api_contract/output/openapi.yaml](stages/02_api_contract/output/openapi.yaml) vs [04_api_build/output/openapi.generated.yaml](stages/04_api_build/output/openapi.generated.yaml) — diff in [contract-deltas.md](stages/04_api_build/output/contract-deltas.md) |
| Auth flow weirdness | [02_api_contract/output/auth-model.md](stages/02_api_contract/output/auth-model.md) |
| Admin portal rejects login | URL must be `https://` — see Quickstart |
| App says "Network error" on a phone | CA not trusted yet — [16_mobile_tls/references/android-trust-onboarding.md](stages/16_mobile_tls/references/android-trust-onboarding.md) |
| `tlsv1 alert internal error` from curl | SNI / `default_sni` — [15_tls_termination/output/run-log.md](stages/15_tls_termination/output/run-log.md) |
| App / cert covers wrong IP (blank admin portal) | Re-run `bash src/scripts/up.sh` — it re-detects the LAN IP and re-issues the cert |
| Screen missing or odd | [05_mobile_design/output/screens.md](stages/05_mobile_design/output/screens.md) → [06_mobile_build/output/screens-built.md](stages/06_mobile_build/output/screens-built.md) |
| DB schema or seed | [03_data_model/output/entities.md](stages/03_data_model/output/entities.md), [src/backend/app/seed.py](src/backend/app/seed.py) |

## Methodology one-pager

This workspace follows the **Model Workspace Protocol (MWP)** described in [docs/MWP.md](docs/MWP.md): folder structure replaces framework orchestration. Each stage's `CONTEXT.md` defines its inputs / process / outputs. Edit `stages/*/references/`, `_config/`, `shared/` to change what every future run does; edit `stages/*/output/` only to record this run. `src/` is the shipping copy; re-sync from stages with `rsync -a --delete` (excluding build artefacts) when stage outputs become canonical again.

## Phase 3 (out of scope)

Threat model, fraud scenarios, controls review — a separate analytical workspace consumes these artefacts. Functional follow-ups deferred from Phase 2 are listed as `OUT-OF-PHASE-2` in [stages/08_phase2_requirements/output/backlog.md](stages/08_phase2_requirements/output/backlog.md): loyalty redemption, admin MFA, supplier portal, push notification inbox, real FCM credentials in CI.
