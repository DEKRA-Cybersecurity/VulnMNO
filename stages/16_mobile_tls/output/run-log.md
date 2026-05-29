# Stage 16 — Run log

## 2026-05-28 — first mobile-TLS bring-up

### Sequence

1. **Caddy host list extended** with `10.0.2.2`:

   ```bash
   docker compose -f src/docker/docker-compose.yml --profile tls restart caddy
   ```

   Caddy log on restart:

   ```
   tls.obtain  acquiring lock identifier="10.0.2.2"
   tls.obtain  obtaining certificate identifier="10.0.2.2"
   tls.obtain  certificate obtained successfully identifier="10.0.2.2" issuer="local"
   ```

2. **SNI cert-selection verification** — confirmed each SNI gets the
   right leaf cert:

   ```
   SNI=10.0.2.2     → X509v3 SAN: IP Address:10.0.2.2
   SNI=192.168.1.98 → X509v3 SAN: IP Address:192.168.1.98
   NO SNI (curl)    → X509v3 SAN: IP Address:192.168.1.98  (via default_sni)
   ```

   Android (Conscrypt on API 26+) sends SNI for IP literals, so the
   emulator gets its 10.0.2.2 cert through the SNI path. The no-SNI
   case is purely a fallback for curl-from-laptop.

3. **Mobile source changes applied** — see `changes-summary.md`.

4. **Compile check** — debug Kotlin sources compile cleanly with the
   JetBrains JBR bundled with Android Studio:

   ```
   JAVA_HOME=/home/d4str3k/tools/android-studio/jbr \
   ./gradlew :app:compileDebugKotlin --no-daemon --console=plain

   > Task :app:kspDebugKotlin
   > Task :app:compileDebugKotlin
   BUILD SUCCESSFUL in 29s
   ```

   The project pins `toolchainVendor=jetbrains` via
   `gradle/gradle-daemon-jvm.properties`. Other vendor JDKs (Debian
   OpenJDK 21) are rejected by Gradle's toolchain check — operators
   must point `JAVA_HOME` at the AS-bundled JBR.

### Status: PASS (build + cert plumbing)

- The mobile sources compile against the new HTTPS default.
- The Caddy proxy serves a SAN-correct cert for the emulator's view
  of the host loopback (`10.0.2.2`).
- The release variant network policy forbids cleartext; the debug
  variant policy is unchanged so the M1 L3 lab stays intact.
- The runtime override truth table is implemented in
  `BaseUrlInterceptor.normalize()` (covered by KDoc; no unit tests
  exist for this file yet — see Known caveats below).

### Not yet verified in this run

- **End-to-end emulator login round-trip after CA install.** Requires
  an AVD running on the host; the harness this run executed in did
  not have an emulator available. The script
  `output/scripts/install_caddy_ca_android.sh` is shipped on the
  assumption that the operator runs it manually as part of the
  quickstart in `output/README.md`. The next operator pass should
  append an entry to this log with the actual login evidence.
- **Physical-device round-trip.** Same caveat. The Caddy cert covers
  `192.168.1.98` by default; if the LAN IP differs, the operator
  must edit `Caddyfile` (or set `VULNMNO_TLS_HOSTS`) and update
  `default_sni` before testing.

### Known caveats / follow-ups

- ~~**`stages/06_mobile_build/output/android/` divergence.**~~
  **Resolved 2026-05-28.** The stages canonical was synced from
  `src/mobile/android/` via:
  ```bash
  rsync -a --delete \
      --exclude '.gradle/' --exclude '.kotlin/' --exclude '.idea/' \
      --exclude 'build/' --exclude 'captures/' \
      --exclude 'local.properties' --exclude '*.iml' \
      src/mobile/android/ stages/06_mobile_build/output/android/
  ```
  In the same pass `stages/04_api_build/output/backend/` was synced
  from `src/backend/` (Python excludes plus `dev.db` / `uploads/`).
  Both stages now reflect the post-stage-16 TLS state.
  Subsequent edits to `src/` will re-introduce drift unless this
  rsync pair is re-run; the workspace does not auto-sync.
- **Toolchain pin to JetBrains JBR.** Trainees without Android
  Studio installed will hit the same Gradle error this run did.
  Either install AS (and point `JAVA_HOME` at its bundled JBR) or
  remove `gradle/gradle-daemon-jvm.properties`'s vendor
  restriction.
- **No automated tests for `BaseUrlInterceptor.normalize()`.** The
  truth table is documented in two places (KDoc + stage references)
  but a one-shot unit test would catch future regressions cheaply.
  Out-of-scope here; flagged.
- **`default_sni` is still `192.168.1.98`.** If the lab moves to a
  different LAN IP, `default_sni` must move with it — otherwise
  curl-from-laptop hits the wrong cert. Android isn't affected
  because it sends SNI.
