#!/usr/bin/env bash
# Extract Caddy's local CA root cert and `adb push` it onto an attached
# Android device / emulator. The user must then walk through the
# Settings flow manually — Android does not allow programmatic user-CA
# installation (it requires explicit human consent, by design).
#
# Prereqs:
#   - The `tls` compose profile is up (`docker compose --profile tls up`).
#   - `adb` is on PATH and a device is attached / emulator is running.
#
# Usage:
#   install_caddy_ca_android.sh [device-path]
#
# Defaults the target on the device to /sdcard/Download/caddy-root.crt.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_ON_DEVICE="${1:-/sdcard/Download/caddy-root.crt}"

if ! command -v adb >/dev/null 2>&1; then
    echo "adb not found on PATH" >&2
    echo "  install via: apt install adb  (or use Android Studio's platform-tools)" >&2
    exit 2
fi

if [[ -z "$(adb devices | awk 'NR>1 && $2=="device" {print $1}')" ]]; then
    echo "no adb device attached. start an emulator or plug in a phone." >&2
    exit 3
fi

LOCAL_PATH="$(mktemp -t caddy-root.XXXXXX.crt)"
trap 'rm -f "$LOCAL_PATH"' EXIT

# Pull the root cert via the sibling helper.
bash "$SCRIPT_DIR/install_caddy_ca.sh" "$LOCAL_PATH" >/dev/null

adb push "$LOCAL_PATH" "$DEST_ON_DEVICE"

cat <<EOF

cert pushed to the device at $DEST_ON_DEVICE.

manual install (cannot be scripted — Android requires user consent):

  1. Settings → Security → Encryption & credentials
     → Install a certificate → CA certificate
  2. Tap "Install anyway" on the monitoring warning.
  3. Pick Internal storage → Download → caddy-root.crt
  4. Name it "VulnMNO Caddy Root", confirm.

verify under Settings → Security → Encryption & credentials
→ Trusted credentials → USER. Once the cert is listed, the app's
https://10.0.2.2/ (emulator) or https://<lan-ip>/ (physical) traffic
will succeed.
EOF
