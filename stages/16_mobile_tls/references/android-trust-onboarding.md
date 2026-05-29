# Trusting the Caddy local CA on Android

The release variant trusts user-installed CAs (see
[`tls-strategy.md`](tls-strategy.md)), so a trainee can reach
`https://10.0.2.2/` (emulator) or `https://<lan-ip>/` (physical
device) once the Caddy root is imported into the device's user
trust store.

## Step 1 — extract the root cert from the running Caddy container

From the repo root, with the `tls` profile up:

```bash
bash stages/15_tls_termination/output/scripts/install_caddy_ca.sh ./caddy-root.crt
```

(Same script as for the laptop browser trust step. The CA is shared
between both surfaces.) The cert is PEM, named subject
`Caddy Local Authority - <year> ECC Root`.

## Step 2a — Android emulator (Android Studio AVD)

```bash
# Push the cert into the emulator's filesystem.
adb push caddy-root.crt /sdcard/Download/caddy-root.crt
```

Then on the emulator UI:

1. **Settings → Security → Encryption & credentials → Install a
   certificate → CA certificate.**
2. Tap **Install anyway** when the warning about monitoring appears
   (user-installed CAs are what we want).
3. Pick **Internal storage → Download → caddy-root.crt**.
4. Name it `VulnMNO Caddy Root` and confirm.
5. Verify under **Settings → Security → Encryption & credentials →
   Trusted credentials → USER** that the cert is listed.

After this, the app's `https://10.0.2.2/` traffic will succeed.

A bundled helper does the push + prints the menu path:

```bash
bash stages/16_mobile_tls/output/scripts/install_caddy_ca_android.sh
```

## Step 2b — physical device on the lab Wi-Fi

```bash
# Phone connected to the host laptop via USB with developer mode on.
adb devices                     # confirm the device id
adb push caddy-root.crt /sdcard/Download/caddy-root.crt
```

Manual flow on the phone is the same as the emulator: Settings →
Security → Install a CA certificate → pick the file → confirm
"Install anyway".

Note: on some OEM ROMs the menu path is slightly different —
"Encryption & credentials" may be nested under "More security
settings" or "Biometrics and security". The key phrase is
**Install a certificate → CA certificate**.

## Step 3 — verify from inside the app

1. Build & install: `./gradlew :app:installDebug`.
2. Launch the app, do NOT touch "Physical device?".
3. Log in with the seeded customer: `+34600000001` / `secret123`.
4. The login succeeds → cert chain verified → user-CA trust working.

If login fails with `SSLHandshakeException`:

- Confirm the cert is listed under **Trusted credentials → USER**.
- Confirm the Caddy container is running: `docker compose --profile
  tls ps caddy`.
- Confirm the Caddyfile host list contains `10.0.2.2` (emulator) or
  the LAN IP (physical).

## When the cert changes

If the Caddy local CA is wiped (`docker volume rm src_caddy_data
src_caddy_config`) or the Caddyfile host list changes, the issued
leaf certs change too. Trainees must:

1. Remove the old "VulnMNO Caddy Root" entry from **Trusted
   credentials → USER**.
2. Re-extract and re-import per Step 1 + Step 2.

The Caddy local CA root key itself only rotates when the
`caddy_data` volume is wiped — under normal operation it persists.

## Trust-store layering (for completeness)

- **System** trust anchors are baked into the ROM. Cannot be
  modified without root.
- **User** trust anchors live under `/data/misc/user/0/cacerts-added`
  and are managed via Settings. This is the layer the Caddy root
  goes into.
- The main `network_security_config.xml` (post stage 16) trusts
  both layers in release; the debug overlay trusts both too.

## Removing the trust (when the lab is done)

**Settings → Security → Encryption & credentials → Trusted
credentials → USER → VulnMNO Caddy Root → Remove**.
