# Trusting the Caddy local CA

After the `tls` profile is up, Caddy is signing leaf certificates with a
self-generated root. Browsers and OS keychains do not trust that root out
of the box. Below: how to extract the root cert and install it on the
platforms a trainer is likely to hit.

## Step 1 — extract the root cert from the container

```bash
bash stages/15_tls_termination/output/scripts/install_caddy_ca.sh ./caddy-root.crt
```

The script `docker exec`s into the running `caddy` container and copies
`/data/caddy/pki/authorities/local/root.crt` to the destination path on
the host. The cert is in PEM form, ~1 KB, named subject
`Caddy Local Authority - <year> ECC Root`.

If the script doesn't fit your workflow:

```bash
docker compose -f src/docker/docker-compose.yml --profile tls \
  exec caddy cat /data/caddy/pki/authorities/local/root.crt > caddy-root.crt
```

## Step 2 — import into a trust store

### Linux (system-wide, Debian / Ubuntu / Kali)

```bash
sudo cp caddy-root.crt /usr/local/share/ca-certificates/vulnmno-caddy-root.crt
sudo update-ca-certificates
```

After this `curl https://192.168.1.98/admin/login` works without `-k`.
Firefox uses its own NSS store and ignores the system CAs — see the
Firefox section below.

### Linux (Fedora / RHEL)

```bash
sudo cp caddy-root.crt /etc/pki/ca-trust/source/anchors/vulnmno-caddy-root.crt
sudo update-ca-trust extract
```

### macOS

```bash
sudo security add-trusted-cert -d -r trustRoot \
    -k /Library/Keychains/System.keychain caddy-root.crt
```

### Windows

PowerShell, elevated:

```powershell
Import-Certificate -FilePath .\caddy-root.crt -CertStoreLocation Cert:\LocalMachine\Root
```

### Firefox (any platform)

`about:preferences#privacy` → **Certificates** → **View Certificates** →
**Authorities** tab → **Import** → select `caddy-root.crt` → check
**Trust this CA to identify websites**.

### Chrome / Edge (Linux)

These use NSS as well. Either install via the system store (works on
some distros) or use `certutil`:

```bash
certutil -d sql:$HOME/.pki/nssdb -A -t "C,," \
    -n "VulnMNO Caddy Root" -i caddy-root.crt
```

## Step 3 (optional) — Android device trust

The mobile app talks plain HTTP to `:8000` and does not need TLS trust.
Only do this if you want a phone's browser to hit the admin portal.

1. Push the cert onto the device: `adb push caddy-root.crt /sdcard/`.
2. **Settings → Security → Encryption & credentials → Install a
   certificate → CA certificate**, pick the file from Downloads, name it
   *VulnMNO Caddy Root*.
3. The device will warn that the network may be monitored. Accept; the
   user-installed CA tier is what we want.

Note: post-Android 7 (API 24+) apps only trust user-installed CAs if
their `network_security_config.xml` opts in. The VulnMNO debug build
does (`stages/06_mobile_build/output/android/app/src/debug/res/xml/network_security_config.xml`
sets `<certificates src="user" />`); the release build does not.

## Revocation / rotation

To force a fresh CA (e.g. you suspect the root key leaked, or you simply
want a clean slate):

```bash
docker compose -f src/docker/docker-compose.yml --profile tls down
docker volume rm src_caddy_data src_caddy_config 2>/dev/null || true
docker compose -f src/docker/docker-compose.yml --profile tls up -d
```

The next start regenerates the root and all leaf certs. Re-run the
extraction + import on every workstation that had the old root.
