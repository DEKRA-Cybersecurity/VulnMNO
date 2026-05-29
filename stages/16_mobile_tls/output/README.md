# Stage 16 — Operator quickstart

The Android client now defaults to **HTTPS via the Caddy reverse-proxy
from stage 15**. The release variant forbids cleartext; both variants
trust user-installed CAs so a trainee can import the Caddy local CA on
the device.

## Build & install (emulator)

```bash
# 1) Bring up the backend + Caddy.
cd src/docker
docker compose --profile tls up -d

# 2) Push Caddy's root cert into the emulator and walk the install flow.
cd $REPO_ROOT
bash stages/16_mobile_tls/output/scripts/install_caddy_ca_android.sh
# follow the on-screen Settings steps.

# 3) Build & install the debug APK.
cd src/mobile/android
./gradlew :app:installDebug
```

The app starts on `BuildConfig.BASE_URL = "https://10.0.2.2/"` (no
"Physical device?" override needed for the emulator).

## Build & install (physical device on the lab Wi-Fi)

Same as above, but:

- Make sure the phone and the host are on the same Wi-Fi.
- The Caddyfile pre-issues a cert covering `192.168.1.98` by default;
  edit `src/docker/Caddyfile` (or set `VULNMNO_TLS_HOSTS=...`) if the
  host's LAN IP differs, then `docker compose --profile tls restart
  caddy`. Also update `default_sni` to match if your client doesn't
  send SNI for IP literals.
- After installing the cert, tap **Physical device?** on the login
  screen and type the host IP (no port → defaults to `https://<ip>:443`
  via Caddy).

## The runtime override truth table

| What you type in "Physical device?" | Resolves to | Comment |
|---|---|---|
| `192.168.1.42` | `https://192.168.1.42:443` | Default. Through Caddy. |
| `192.168.1.42:443` | `https://192.168.1.42:443` | Same as above, explicit. |
| `192.168.1.42:8000` | `http://192.168.1.42:8000` | **Cleartext.** Direct to backend. Downgrade-lab path (M1 L3). |
| `192.168.1.42:9000` | `https://192.168.1.42:9000` | Any other explicit port stays HTTPS. |
| `http://host[:port]` | as typed | Explicit scheme honoured. |
| `https://host[:port]` | as typed | Explicit scheme honoured. |

The `:8000` → HTTP heuristic is deliberate. It's the natural reading
of "port 8000 is the backend's plain port"; it preserves the M1 L3
downgrade lab; and it gives a non-cryptic way to opt into cleartext
when intentional.

## Variants — what changed where

| File | Before | After |
|---|---|---|
| `app/build.gradle.kts` (debug + release `BASE_URL`) | `http://10.0.2.2:8000` | `https://10.0.2.2/` |
| `app/src/main/AndroidManifest.xml` | `android:usesCleartextTraffic="true"` | attribute removed |
| `app/src/main/res/xml/network_security_config.xml` | per-domain cleartext for `10.0.2.2`/`localhost`/`127.0.0.1` | `cleartextTrafficPermitted="false"`, trusts system + user CAs |
| `app/src/debug/res/xml/network_security_config.xml` | (unchanged) | **unchanged on purpose** — keeps the M1 L3 finding discoverable on debug builds |
| `BaseUrlInterceptor.kt` | bare host → `http://host:8000` | bare host → `https://host:443`, `:8000` → `http`, all other ports → `https` |

## Verification

```bash
# Cert SAN per SNI (from the laptop)
echo | openssl s_client -connect 127.0.0.1:443 -servername 10.0.2.2 2>/dev/null \
  | openssl x509 -noout -ext subjectAltName | grep '10.0.2.2'

# Login round-trip from the running emulator after CA import:
# (use the app UI — the JSON path is:)
#   POST https://10.0.2.2/api/auth/login   (HTTPS)
#       body: {"msisdn":"+34600000001","password":"secret123"}
#   200 OK -> accessToken / refreshToken
# Inspect with mitmproxy in regular mode to confirm the TLS is
# terminated at Caddy (you see the upstream as backend:8000 unencrypted
# on the Docker network only — never on the device-laptop wire).
```

## Downgrade-lab fast path (for the M1 L3 exercise)

```bash
# Rebuild with the old cleartext default:
cd src/mobile/android
./gradlew assembleDebug \
    -PBASE_URL_DEBUG="http://10.0.2.2:8000"
./gradlew :app:installDebug
# OR: leave the build alone, just type "192.168.1.42:8000" in
# "Physical device?" on the login screen.
```

Either flips the runtime to cleartext; everything else (the permissive
debug `network_security_config`, the user-CA trust, the OkHttp
`HttpLoggingInterceptor`) stays in place to support the lab.

## What this stage does **not** change

- The backend's listening port — `backend:8000` is still published.
  The mobile app reaches it via Caddy:443 by default, but a curl from
  the LAN can still hit `:8000` directly.
- The debug network policy. It still permits cleartext + user CAs.
- The OTP brute-force vuln, the DataStore plaintext token storage,
  or any other seeded lab finding. Those are independent and untouched.
- Public-CA-signed certs. Still `tls internal`.
- Cert pinning. Deliberately omitted — keeps the M3 user-CA-MITM
  surface alive.

See `references/tls-strategy.md` for the decision record and
`references/android-trust-onboarding.md` for the cert-install flow.
The first run-through is captured in `run-log.md`.
