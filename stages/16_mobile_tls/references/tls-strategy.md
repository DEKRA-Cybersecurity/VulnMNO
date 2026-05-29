# Mobile TLS strategy

## Decision

Default the Android client to HTTPS via the Caddy reverse-proxy from
stage 15. Tighten the *main* / release network security policy to forbid
cleartext entirely. **Trust user-installed CAs in both main and debug**
so a trainee can import the Caddy local CA on the device.

Keep the *debug* variant policy permissive (cleartext + user CAs)
so the M1 L3 training surface remains discoverable via static
analysis on debug builds.

## Truth table for the runtime override

`BaseUrlInterceptor.normalize()` resolves whatever the user types into
"Physical device?" with the following rules:

| Input | Scheme | Port | Comment |
|---|---|---|---|
| `192.168.1.42` | https | 443 | Default. Goes through Caddy. |
| `192.168.1.42:443` | https | 443 | Explicit-port HTTPS. |
| `192.168.1.42:8000` | http | 8000 | **Downgrade.** Bypasses Caddy, hits the backend's direct HTTP port. The M1 L3 / M3 downgrade lab path. |
| `192.168.1.42:9000` | https | 9000 | Any other explicit port stays HTTPS. |
| `http://host[:port]` | http | as typed | Explicit scheme honoured. |
| `https://host[:port]` | https | as typed | Explicit scheme honoured. |

The `:8000` → HTTP heuristic is deliberate. It preserves the downgrade
exploit for the M1 L3 lab without forcing the trainee to type the full
`http://` prefix — and it matches the natural reading of "8000 is the
backend's plain port, 443 is Caddy's TLS port."

## Why not …

| Alternative | Why rejected |
| --- | --- |
| **Cert pinning (OkHttp `CertificatePinner`)** | The Caddy local CA regenerates its leaf cert any time the LAN IP changes; a static pin would break every relocation. More importantly the absence of pinning is itself an M3 finding the lab wants to keep discoverable. |
| **Drop `<certificates src="user" />` in main** | Then a release APK could not reach the Caddy proxy because the local CA is not in the system store on unrooted devices. Either we trust user CAs (this stage's choice) or we accept the release variant is HTTPS-incapable on the lab network. |
| **System CA install via Magisk module / rooted emulator** | Forces rooted devices on every trainee. Too high a barrier for a training lab. |
| **Use the public ACME (Let's Encrypt)** | Caddy proxy is on a private IP. Public ACME would not issue. mkcert in front would help the laptop but not Android (still needs user-CA import). |
| **Make the app HTTPS-only with no `:8000` downgrade path** | Kills the M1 L3 lab — the cleartext finding becomes purely theoretical because the app has no way to actually emit cleartext. Defeats the workspace's training purpose. |

## Why the debug policy stays permissive

The CLAUDE.md scope explicitly carves out vulnerability seeding as the
intended workspace outcome. The L3 finding in
[`src/docs/vulns/mobile/M1-Improper-Credential-Usage.md`](../../../src/docs/vulns/mobile/M1-Improper-Credential-Usage.md)
relies on the debug variant's
`cleartextTrafficPermitted="true"` + `<certificates src="user" />`
combination being statically observable in the decoded APK. If we
tightened debug to match release, that finding would vanish from the
training material.

The static analysis path stays the same:

1. `apktool d app-debug.apk`
2. `cat vulnmno-decoded/res/xml/network_security_config.xml`
3. Spot `cleartextTrafficPermitted="true"` at base-config level.

What changed is the *exploit*: it used to be "the app already speaks
HTTP by default, just sniff the wire". Now it is "the policy *permits*
HTTP, but you have to flip the default — either at runtime via the
override or at build time via `-PBASE_URL_DEBUG=http://...`". Both
paths are documented in the refined M1 doc.

## Why user-CA trust is propagated to release

This is the load-bearing trade-off of the stage. Three options:

1. **Distribute the Caddy root with the APK and pin it.** Maximum
   security, but every cert rotation breaks every device. Wrong for a
   training lab where IPs change.
2. **Drop user-CA trust in release.** Then the release APK is unusable
   on the lab network unless trainees have a rooted device.
3. **Trust user CAs in release.** The release APK is reachable after
   a one-time CA import; trade-off is the release variant is
   MITM-able with any installed CA. This is the chosen path and the
   trade-off is documented in the M3 doc as an intentional weakness.

Stage 16 picks (3). A trainee assignment can later "harden" the app
by removing user-CA trust and adding a pin — that is the remediation
exercise.

## Failure modes & remedies

| Symptom | Cause | Remedy |
| --- | --- | --- |
| App throws `SSLHandshakeException: Trust anchor for certification path not found` | Caddy local CA not imported in the device's user trust store | Run `scripts/install_caddy_ca_android.sh` and walk through Settings → Security → Install a CA cert |
| App connects but cert says wrong IP | Caddy issuing for a hostname not in `Caddyfile`'s host list | Add the LAN IP / DNS name to `VULNMNO_TLS_HOSTS` (or the hard-coded list) and `docker compose --profile tls restart caddy` |
| Login still works over plain HTTP from the emulator | `BASE_URL_DEBUG` overridden via `-P` or a stale runtime override is set in DataStore | Inspect `BuildConfig.BASE_URL` in `adb logcat`; clear the override via the login screen's "Use default" button |
| Release APK cannot reach Caddy even after CA import | Release variant build has the manifest's old `usesCleartextTraffic="true"` — rebuild from the post-stage-16 sources | `./gradlew :app:assembleRelease` after pulling the stage-16 changes |
| Static-analysis lab no longer shows the L3 cleartext finding | A trainee analysed a release APK instead of debug | Lab instructions must explicitly call for `app-debug.apk` (the policy under analysis lives in `src/debug/`) |
