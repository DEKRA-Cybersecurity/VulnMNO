#!/usr/bin/env bash
# Extract Caddy's local CA root cert and push it onto an attached Android
# device / emulator so the user can install it as a user-trust CA.
#
# Prereqs:
#   - The `tls` compose profile is up (`docker compose --profile tls up`).
#   - `adb` is on PATH and a device is attached / emulator is running.
#
# Usage:
#   install_caddy_ca_android.sh [device-path]
#
# Defaults the target path on the device to /sdcard/Download/caddy-root.crt.
# After push, prints the Settings flow the user must walk through manually
# (Android does not allow programmatic user-CA installation).

set -euo pipefail

DEST_ON_DEVICE="${1:-/sdcard/Download/caddy-root.crt}"
LOCAL_PATH="$(mktemp -t caddy-root.XXXXXX.crt)"
COMPOSE_FILE="${VULNMNO_COMPOSE_FILE:-src/docker/docker-compose.yml}"

if ! command -v adb >/dev/null 2>&1; then
    echo "adb not found on PATH" >&2
    exit 2
fi

if [[ -z "$(adb devices | awk 'NR>1 && $2=="device" {print $1}')" ]]; then
    echo "no adb device attached. start an emulator or plug in a phone." >&2
    exit 3
fi

# Pull the root cert via the stage-15 helper.
bash "$(dirname "$0")/../../../15_tls_termination/output/scripts/install_caddy_ca.sh" "$LOCAL_PATH"

adb push "$LOCAL_PATH" "$DEST_ON_DEVICE"
rm -f "$LOCAL_PATH"

cat <<EOF

cert pushed to the device at $DEST_ON_DEVICE.

manual install (cannot be scripted — Android requires user consent):

  1. Open Settings → Security → Encryption & credentials
     → Install a certificate → CA certificate
  2. Tap "Install anyway" on the monitoring warning.
  3. Pick Internal storage → Download → caddy-root.crt
  4. Name it "VulnMNO Caddy Root", confirm.

verify under Settings → Security → Encryption & credentials
→ Trusted credentials → USER. Once the cert is listed, the app's
https://10.0.2.2/ (emulator) or https://<lan-ip>/ (physical) traffic
will succeed.

full menu paths + troubleshooting in
stages/16_mobile_tls/references/android-trust-onboarding.md
EOF
