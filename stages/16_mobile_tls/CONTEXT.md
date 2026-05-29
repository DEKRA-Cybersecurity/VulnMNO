# Stage 16 — Mobile client over TLS

Bring the Android client into line with `docs/VulnMNO.md` §7.1
("The app communicates with the backend using HTTPS-based REST APIs")
by switching the default base URL to HTTPS and routing through the
Caddy reverse-proxy added in stage 15. Tighten the main /
release network security policy to forbid cleartext. Preserve the
M1 L3 training surface by leaving the *debug* variant policy and
the runtime downgrade path intact.

## Inputs

**Layer 4 (working):**

- `../15_tls_termination/output/Caddyfile` — host list extended
  with `10.0.2.2` so the emulator's loopback alias gets its own
  leaf cert.
- `../15_tls_termination/output/docker-compose.yml` — `tls` profile
  this stage relies on at runtime.
- `../06_mobile_build/output/android/` — canonical Android project
  (out-of-sync vs `src/mobile/android/`; see run-log note).
- `../../src/mobile/android/` — actually-built copy. **This is the
  set of files this stage edits.**
- `../../src/docs/vulns/mobile/M1-Improper-Credential-Usage.md` — L3
  section gets refined to reflect the new default and the new
  downgrade exploit path.

**Layer 3 (reference):**

- `references/tls-strategy.md` — decisions: HTTPS default,
  user-CA trust kept as a deliberate M3 surface, no cert pinning.
- `references/android-trust-onboarding.md` — extract Caddy local CA,
  push to device, install via Settings (emulator + physical).
- `../15_tls_termination/references/tls-strategy.md` — companion
  decision record for the server-side termination.

## Process

1. **Caddy host list** — add `10.0.2.2` to the site addresses in
   `src/docker/Caddyfile` so the emulator reaches a SAN-correct cert
   via SNI. Verify with `openssl s_client -servername 10.0.2.2`.
2. **`BASE_URL_DEBUG` / `BASE_URL_RELEASE` defaults** — flip to
   `https://10.0.2.2/` in `app/build.gradle.kts`. Both variants now
   default to HTTPS via the Caddy proxy.
3. **`BaseUrlInterceptor.normalize()`** — implement the truth table
   that turns user-typed "Physical device?" overrides into URLs:
   bare host → HTTPS:443, explicit `:8000` → HTTP:8000 (the M1/M3
   downgrade lab), explicit `:443` → HTTPS:443, scheme prefix → as-is.
4. **Main network security policy** — rewrite
   `app/src/main/res/xml/network_security_config.xml` to
   `cleartextTrafficPermitted="false"` and trust system + user CAs.
   Remove `android:usesCleartextTraffic="true"` from the manifest.
5. **Debug variant untouched** — `app/src/debug/res/xml/network_security_config.xml`
   keeps `cleartextTrafficPermitted="true"` so M1 L3 stays
   discoverable via static analysis on debug builds.
6. **M1 doc refinement** — update L3 in
   `src/docs/vulns/mobile/M1-Improper-Credential-Usage.md` to
   describe the new compile-time default, the truth-table downgrade
   path, and the rebuild downgrade path.
7. **CA install helper** — ship
   `output/scripts/install_caddy_ca_android.sh` that extracts the
   Caddy root via the stage-15 script, pushes it via `adb push`, and
   prints the manual Settings flow.
8. **Compile check** — `./gradlew :app:compileDebugKotlin` (with the
   Android Studio bundled JBR — the project pins
   `toolchainVendor=jetbrains`) must stay green.
9. **README update** — `src/README.md` mobile section reflects the
   HTTPS default and points at the CA-install helper.
10. Record evidence in `output/run-log.md`.

## Outputs

- `output/README.md` — operator quickstart (build + CA install +
  emulator verification + fallback to HTTP for the downgrade lab).
- `output/changes-summary.md` — file-by-file diff inventory.
- `output/run-log.md` — first-run evidence: SNI cert verification,
  compile result, manual emulator login round-trip.
- `output/scripts/install_caddy_ca_android.sh` — adb helper.
- Touched canonical runtime files (not under `output/`):
  - `src/docker/Caddyfile` — `10.0.2.2` added to host list.
  - `src/mobile/android/app/build.gradle.kts`
  - `src/mobile/android/app/src/main/AndroidManifest.xml`
  - `src/mobile/android/app/src/main/res/xml/network_security_config.xml`
  - `src/mobile/android/app/src/main/java/com/vulnmno/app/data/remote/BaseUrlInterceptor.kt`
  - `src/mobile/android/app/src/main/java/com/vulnmno/app/ui/screens/auth/AuthScreens.kt`
  - `src/docs/vulns/mobile/M1-Improper-Credential-Usage.md`
  - `src/README.md`

## Out of scope

- Certificate pinning. Intentionally not added — keeps the user-CA
  MITM surface for M3 labs (covered in
  `src/docs/vulns/mobile/M3-Insecure-Authentication-Authorization.md`).
- Public-CA-signed certificates. `tls internal` is the right answer
  for a training LAN.
- Sync of `BaseUrlStore.kt` / `BaseUrlInterceptor.kt` /
  `src/debug/` from `src/mobile/android/` back to
  `stages/06_mobile_build/output/android/`. That divergence
  pre-existed this stage; squaring it is a separate task — flagged
  in `run-log.md`.
- Public-network deployment. The TLS profile is configured for a
  LAN training stack; production hardening (HSTS, OCSP stapling,
  public ACME, cert pinning) belongs to a later phase.
