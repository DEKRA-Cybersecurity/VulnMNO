# Setup questionnaire

Answer these once at the start of a run. Stages read your answers from this file. Format choices are in `_config/` — do not put them here.

## 1. Phase identity

- **Phase name:** _e.g. `phase-1-full-journeys`_
- **Date (ISO):** _e.g. 2026-05-26_
- **Operator initials:** _e.g. DPS_

## 2. Scope confirmation

- **Journeys to include** (default = §9.1 through §9.6): _override if reducing scope mid-phase_
- **Endpoint groups to include** (default = auth, customers, accounts, shop, plans, usage, support, notifications): _override if reducing_
- **Out of phase 1 explicitly:** Administration portal (§7.13), real payment gateway, real provisioning, push delivery, i18n.

## 3. Local run configuration

- **Backend port:** 8000
- **Backend DB for dev:** SQLite at `stages/04_api_build/output/backend/dev.db`
- **Android emulator base URL:** `http://10.0.2.2:8000` (Android emulator → host loopback)
- **Physical-device base URL:** _set to your machine's LAN IP, e.g. `http://192.168.1.20:8000`_

## 4. Seed data

- **Number of seeded customers:** 3 (one prepaid, one postpaid, one hybrid)
- **Seed promo codes:** at least one valid (`STACK5`), one expired
- **Seed plans:** prepaid basic, prepaid plus, unlimited premium
- **Seed bundles:** `DATA-10GB-7D`, `ROAMING-EU`

## 5. Build variants

- **Backend variants:** `dev` (SQLite, verbose logging), `prod-like` (PostgreSQL via docker-compose, structured JSON logs).
- **Android variants:** `debug` (points at `10.0.2.2:8000`), `release` (BASE_URL injected at build time).

## 6. Deliverable definition of "phase 1 done"

Phase 1 is done when stage 07 produces a passing end-to-end run for **every** journey in §9.1–§9.6 against the seeded data, executed from the Android app running in the emulator.
