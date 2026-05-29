# Stage 16 — Changes summary

File-by-file diff inventory. All changes target the **shipping copy**
under `src/`; the stage `references/` and `output/` are documentation
and snapshots.

## Mobile sources (`src/mobile/android/`)

### `app/build.gradle.kts`

- `BASE_URL_DEBUG` default: `http://10.0.2.2:8000` → `https://10.0.2.2/`
- `BASE_URL_RELEASE` default: `http://10.0.2.2:8000` → `https://10.0.2.2/`

Build-time override via `-PBASE_URL_DEBUG=...` still works (used by
the M1 L3 downgrade lab).

### `app/src/main/AndroidManifest.xml`

- Removed: `android:usesCleartextTraffic="true"`.
- Retained: `android:networkSecurityConfig="@xml/network_security_config"`
  — the config is now the authoritative cleartext policy.

### `app/src/main/res/xml/network_security_config.xml`

Rewritten from a per-domain cleartext allowlist
(`10.0.2.2`, `localhost`, `127.0.0.1`) to a base-config
`cleartextTrafficPermitted="false"` with `<trust-anchors>` covering
`system` **and** `user`. The user-CA trust is the load-bearing
trade-off — see `references/tls-strategy.md` for the rationale.

### `app/src/debug/res/xml/network_security_config.xml`

**Untouched on purpose.** Debug variant still has
`cleartextTrafficPermitted="true"` + user CAs trusted, so the M1 L3
static-analysis finding remains discoverable on debug APKs.

### `app/src/main/java/com/vulnmno/app/data/remote/BaseUrlInterceptor.kt`

Rewrote `normalize()` to implement the truth table documented in
`references/tls-strategy.md`:

```
bare host         → https://host:443
host:443          → https://host:443
host:8000         → http://host:8000          (downgrade lab path)
host:<other>      → https://host:<other>
http://...        → as typed
https://...       → as typed
```

KDoc updated with the same table.

### `app/src/main/java/com/vulnmno/app/ui/screens/auth/AuthScreens.kt`

- Placeholder hint on the "Physical device?" text field:
  `e.g. 192.168.1.42:8000` → `192.168.1.42  (https/443 via Caddy)`.
  Surfaces the new default to the operator typing the address.

## Docker / reverse-proxy (`src/docker/`)

### `Caddyfile`

- Added `10.0.2.2` to the host list of the HTTPS site block so the
  emulator's loopback alias gets a SAN-correct leaf cert. Now reads:
  `{$VULNMNO_TLS_HOSTS:192.168.1.98 10.0.2.2 localhost 127.0.0.1}`.
- `default_sni 192.168.1.98` left unchanged — affects only no-SNI
  clients (curl from the laptop). Android/OkHttp on API 26+ sends SNI
  for IP literals, so the emulator gets its 10.0.2.2 cert via SNI.

## Training docs (`src/docs/vulns/mobile/`)

### `M1-Improper-Credential-Usage.md`

- L3 section rewritten to describe the post-stage-16 state:
  - Compile-time default is HTTPS via Caddy; static-analysis finding
    of `cleartextTrafficPermitted="true"` on debug remains valid.
  - User-CA trust now propagated to main / release (intentional;
    documented as an M3 surface).
  - Two new exploit paths documented:
    1. Runtime override → `:8000` (interceptor truth table linked).
    2. Build-time `-PBASE_URL_DEBUG=http://...` rebuild.

## Repo-root docs

### `src/README.md`

Mobile section updated to surface the new HTTPS-default behaviour and
point at this stage's CA-install helper.

## What was NOT changed

- `stages/06_mobile_build/output/android/` — the canonical Android
  copy per CLAUDE.md is out-of-sync with `src/mobile/android/`
  (missing `BaseUrlStore.kt`, `BaseUrlInterceptor.kt`, and the
  `src/debug/` directory from a prior phase). That divergence
  pre-existed this stage and is flagged in `run-log.md` as a separate
  follow-up.
- The OkHttp client construction in `NetworkModule.kt`. Interceptor
  chain order is unchanged; the URL rewrite still happens before
  authentication.
- Backend code. The FastAPI service does not know or care whether
  traffic arrived over HTTP:8000 or HTTPS:443 (Caddy → backend:8000)
  — `X-Forwarded-Proto: https` is forwarded for any code that later
  needs it.
