#!/usr/bin/env bash
# Extract the Caddy local-CA root cert out of the running `caddy` container
# so the operator can import it into a workstation trust store (browser /
# system keychain). This root is IP-independent — it's the same authority
# that signs every leaf cert (your detected LAN IP, `10.0.2.2`, `localhost`,
# `127.0.0.1`), so you import it once and it stays valid across networks.
#
# Usage:
#   install_caddy_ca.sh [destination-path]
#
# Defaults the destination to ./caddy-root.crt. Requires the `tls`
# compose profile to be up (`docker compose --profile tls up -d`).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${VULNMNO_COMPOSE_FILE:-$SCRIPT_DIR/../docker/docker-compose.yml}"
DEST="${1:-./caddy-root.crt}"

if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "compose file not found at $COMPOSE_FILE" >&2
    echo "  override with VULNMNO_COMPOSE_FILE=/path/to/docker-compose.yml" >&2
    exit 2
fi

if ! docker compose -f "$COMPOSE_FILE" --profile tls ps caddy --status running --quiet | grep -q .; then
    echo "the 'caddy' service is not running." >&2
    echo "bring it up first:" >&2
    echo "  docker compose -f $COMPOSE_FILE --profile tls up -d" >&2
    exit 3
fi

docker compose -f "$COMPOSE_FILE" --profile tls exec -T caddy \
    cat /data/caddy/pki/authorities/local/root.crt > "$DEST"

echo "wrote $(wc -c < "$DEST") bytes to $DEST"
echo
echo "import into a trust store (pick one):"
echo "  Debian / Ubuntu / Kali:"
echo "    sudo cp '$DEST' /usr/local/share/ca-certificates/vulnmno-caddy-root.crt"
echo "    sudo update-ca-certificates"
echo "  Fedora / RHEL:"
echo "    sudo cp '$DEST' /etc/pki/ca-trust/source/anchors/vulnmno-caddy-root.crt"
echo "    sudo update-ca-trust extract"
echo "  macOS:"
echo "    sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain '$DEST'"
echo "  Firefox / Chrome (NSS):"
echo "    certutil -d sql:\$HOME/.pki/nssdb -A -t 'C,,' -n 'VulnMNO Caddy Root' -i '$DEST'"
