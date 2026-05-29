# VulnMNO — source tree

`src/` is the runnable product. `stages/` (sibling at repo root) is MWP
design history — not required to start the lab.

```
src/
├── backend/        FastAPI + admin portal + Alembic migrations
├── mobile/android/ Kotlin + Jetpack Compose client (minSdk 26)
├── docker/         Dockerfile + docker-compose.yml + Caddyfile
└── scripts/        smoke tests + Caddy CA install helpers
```

## 1. Start the stack

```bash
bash src/scripts/up.sh
```

Brings up Postgres, the FastAPI backend, and a Caddy reverse-proxy that
terminates TLS with a local CA. The script **auto-detects this machine's
LAN IP** and configures Caddy to serve a valid cert for it — so HTTPS
works on any network with no edits. Re-run it after changing networks
(new Wi-Fi, VPN on/off). `bash src/scripts/up.sh down` stops the stack.

Detection is Linux-native (uses `ip`) and is VPN-aware. If it guesses
wrong — on macOS / WSL2, or a setup it can't read — force the IP:

```bash
bash src/scripts/up.sh 192.168.1.50      # use this IP instead of detecting
```

Prefer plain Compose? `cd src/docker && docker compose --profile tls up
-d --build` works too, but only covers `localhost` + the emulator
(`10.0.2.2`) **and** silently reuses any `docker/.env` left by a previous
`up.sh` run (possibly a stale IP) — delete it first, or just use `up.sh`.
Without `--profile tls` you still get the backend on `:8000`, but the
browser admin portal rejects login (its session cookie is `Secure` —
needs HTTPS).

| URL | Purpose |
|---|---|
| `http://<host>:8000/api/*`  | JSON API (Android client target) |
| `http://<host>:8000/docs`   | OpenAPI / Swagger |
| `https://<host>/admin/`     | Admin portal (browser only) |

Seed credentials:

- Admin portal: `ops` / `admin1234`
  (also `support`, `billing`, `product`, `security` — same password)
- Customer login: `+34600000001` / `secret123` (also `…02`, `…03`)
- OTP code (login for `+34600000002`): `123456`
- Password-reset code (any customer): `123456`

## 2. Trust the Caddy CA on your laptop (browser)

Caddy signs with a local CA your browser doesn't know. Accept the cert
warning once, or import the root permanently:

```bash
bash src/scripts/install_caddy_ca.sh       # writes ./caddy-root.crt
# the script prints the OS-specific import command — pick yours.
```

## 3. Build & install the Android client

```bash
cd src/mobile/android
./gradlew :app:installDebug                # emulator or attached phone
```

Default base URL is `https://10.0.2.2/` (emulator → host loopback,
through Caddy). Before the first login on any device you have to
import the Caddy root into the device's user trust store:

```bash
bash src/scripts/install_caddy_ca_android.sh   # adb push + on-screen instructions
```

For a **physical phone** on the lab Wi-Fi: tap **Physical device?**
on the login screen and type the host's LAN IP (the one `up.sh` printed
as "Detected LAN IP"). Resolution rules:

| You type | Effect |
|---|---|
| `<lan-ip>` (or `:443`)  | HTTPS via Caddy (default) |
| `<lan-ip>:8000`         | Plain HTTP direct to backend — M1 L3 downgrade lab |
| `http://…` / `https://…`    | As typed |

You do **not** edit the Caddyfile for this: `up.sh` already added your
LAN IP to Caddy's cert list. If you moved networks, just re-run
`bash src/scripts/up.sh` and Caddy re-issues a cert for the new IP.

## 3b. Intercept the app with Burp (MITM)

Both the debug and release network-security configs trust **user** CAs
and there is no certificate pinning (deliberate lab weakness — see
[M3](docs/vulns/mobile/M3-Insecure-Authentication-Authorization.md)), so
you can MITM the app **without root**.

1. **Burp listener** on `<lan-ip>:8080`. Set the phone's Wi-Fi proxy to
   `<lan-ip>:8080`.
2. **Install Burp's CA in the device *user* store.** Export it (or grab
   it through the proxy: `curl -x http://<lan-ip>:8080 http://burp/cert
   -o burp.der`, `adb push burp.der /sdcard/Download/burp-ca.crt`), then
   on the phone: *Settings → Security → Encryption & credentials →
   Install a certificate → **CA certificate*** (not the generic "install
   from storage" — apps ignore that one).
3. **Point the app at the `nip.io` hostname, not the IP.** In the app:
   **Change → `<lan-ip>.nip.io`** (the value `up.sh` prints as
   "MITM (Burp)"). Then log in — Burp now decrypts the traffic.

Why the hostname: OkHttp requires an `iPAddress` SAN when the target is a
bare IP, but Burp only issues a `DNS`-type SAN for it → handshake
rejected ("Network error"). A hostname makes Burp's `DNS` SAN match.
`up.sh` adds `<lan-ip>.nip.io` to Caddy's cert/host list for this; with
the proxy on, Burp (not the phone) resolves the name.

**Cleartext shortcut** (M1 L3, no cert needed): **Change →
`<lan-ip>:8000`** captures credentials in plaintext straight through
Burp. Switch the override back to `<lan-ip>` for normal HTTPS use.

## 4. Smoke checks (optional)

```bash
BASE_URL=http://localhost:8000 src/scripts/smoke_api.sh    # customer journeys
BASE_URL=http://localhost:8000 src/scripts/smoke_admin.sh  # admin + loyalty + i18n
```

## 5. Generate a log dataset (blue-team / LLM lab)

Fill the backend log with realistic multi-user traffic and bury an OTP
brute-force in it, then capture it for log-analysis practice:

```bash
python3 src/scripts/simulate_traffic.py --benign-sessions 120 --attack-attempts 800
docker logs -t docker-backend-1 > traffic.log 2>&1     # -t = timestamps; 2>&1 = both streams
```

The attacker IP / victim / time window land in `traffic-groundtruth.json` for
grading. Why and how it's built: [M3 write-up](docs/vulns/mobile/M3-Insecure-Authentication-Authorization.md#generating-a-log-dataset).

## Database access

PostgreSQL 16 in `docker-db-1`, exposed on `localhost:5432`. Credentials,
db name, user — all `vulnmno`.

```bash
docker exec -it docker-db-1 psql -U vulnmno -d vulnmno   # no password
# or from the host:
PGPASSWORD=vulnmno psql -h localhost -U vulnmno -d vulnmno
```

GUI clients (DBeaver, pgAdmin, TablePlus): host `localhost`, port `5432`,
db / user / password all `vulnmno`.

Useful starter queries:

```sql
\dt                                              -- list tables
SELECT public_id, primary_msisdn, otp_fixed_code FROM customers;
SELECT id, customer_id, attempts, consumed_at    -- OTP brute-force lab signal
  FROM otp_challenges ORDER BY id DESC LIMIT 10;
SELECT event_type, actor_id, target_id, created_at
  FROM audit_events ORDER BY created_at DESC LIMIT 20;
```

Codes (`otp_challenges.code_hash`, `password_resets.code_hash`) are
SHA-256 hashed — not recoverable from the DB. The fixed lab codes
(`123456` for OTP login of `+34600000002`, `123456` for any password
reset) live in `app/seed.py` and `app/config.py`; the random fallback
(if you turn the fixed code off) is logged by the backend
(`docker logs docker-backend-1 | grep -E 'OTP|PWRESET'`).

For the no-Docker dev path the DB is SQLite at `src/backend/dev.db` —
open with `sqlite3 dev.db` or any viewer.

## Without Docker (backend only, SQLite)

```bash
cd src/backend
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev] && alembic upgrade head
uvicorn app.main:app --reload
```

Set `VULNMNO_ENV=dev` to drop the `Secure` cookie flag so the admin
portal works over plain HTTP for local development.

## Driver flags

Override these in `docker/docker-compose.yml` to exercise real
gateways instead of the bundled `dev` mocks: `VULNMNO_PAYMENT_DRIVER`,
`VULNMNO_PROVISIONING_DRIVER`, `VULNMNO_PUSH_DRIVER`,
`VULNMNO_DEFAULT_LOCALE`, `VULNMNO_RATE_LIMIT_ENABLED`. Defaults work
offline.

## Design history

Each feature has a numbered stage under `stages/` with `CONTEXT.md`,
`references/`, and `output/` (run-log + artefacts). TLS plumbing
lives in `stages/15_tls_termination/` and `stages/16_mobile_tls/`.
