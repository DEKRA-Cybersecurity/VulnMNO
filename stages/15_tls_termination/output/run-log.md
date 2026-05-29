# Stage 15 — Run log

## 2026-05-28 — first TLS bring-up

### Action

```
cd src/docker
docker compose --profile tls up -d caddy
```

### What happened

1. Image `caddy:2-alpine` pulled (v2.11.3).
2. Named volumes `docker_caddy_data` and `docker_caddy_config` created.
3. Caddy started, parsed the Caddyfile, generated a fresh local CA, and
   issued leaf certificates for `192.168.1.98`, `localhost`, and
   `127.0.0.1` (all with the local issuer).
4. Container listening on `0.0.0.0:80` (HTTP, redirect-only) and
   `0.0.0.0:443` (HTTPS, reverse-proxy to `backend:8000`).

### Iteration — `default_sni` was needed

First verification pass failed with `TLS alert internal error` whenever
the client targeted an IP literal (`192.168.1.98` or `127.0.0.1`).
Working through it:

- `openssl s_client -servername 192.168.1.98` → handshake fine.
- `curl https://192.168.1.98` → `tlsv1 alert internal error`.
- `curl https://localhost` (DNS name, sends SNI) → 200.

Root cause: per RFC 6066, SNI is a DNS name only — neither curl nor
mainstream browsers send SNI when the URL host is an IP literal. Caddy
then has no name to match against its configured cert pool and aborts.

Fix: added `default_sni 192.168.1.98` to the global options block in
`src/docker/Caddyfile`, so Caddy substitutes that SNI when none is
received from the client. Snapshot in
`stages/15_tls_termination/output/Caddyfile` was synced to match.

```bash
docker compose --profile tls restart caddy
```

### Verification (post-fix)

```
=== 1. HTTP→HTTPS redirect ===
HTTP /admin/login → 308  Location: https://192.168.1.98/admin/login

=== 2. HTTPS GET /admin/login ===
status=200
csrf=D-7shjk5eFK3JmyTas4hL0M1xfnDmHw93lk0Nwx0F8I

=== 3. POST creds ===
status=303  redirect=https://192.168.1.98/admin/

=== 4. Authenticated dashboard ===
status=200
title: <title>Dashboard · VulnMNO admin
markers: ADM-10004, ops_admin, Sign out

=== 5. Cert details ===
issuer=CN=Caddy Local Authority - ECC Intermediate
X509v3 Subject Alternative Name: critical
    IP Address:192.168.1.98

=== 6. Cookie persisted across the round-trip with Secure flag set ===
vulnmno_admin_session=eyJjc3JmIjogIi…ImFkbWluIjogeyJpZCI6IDQsICJwdWJsaWNfaWQiOiAiQURNLTEwMDA0Iiwgi…(HttpOnly+Secure)
```

Decoded session payload (signed, not encrypted): role `ops_admin`,
public_id `ADM-10004` — exactly what stage 11's seed expected.

### Status: PASS

- HTTPS reachable from the LAN on `https://192.168.1.98/`.
- HTTP requests on port 80 308-redirect to HTTPS.
- The admin portal `Secure` session cookie now survives the round-trip
  (it was being dropped by browsers/curl when the page came over HTTP).
- Backend container unchanged; no application-level config touched.
- Phase-1/2 smoke (mobile API on `:8000` direct, plain HTTP) was not
  regressed — backend port stayed published as `8000:8000`.

### Known caveats

- The cert chain ends at Caddy's local authority. Browsers / OS show a
  trust warning until the operator imports the root via
  `scripts/install_caddy_ca.sh`. This is expected for a training LAN.
- The hardcoded list `192.168.1.98 localhost 127.0.0.1` in the
  Caddyfile is the default — set `VULNMNO_TLS_HOSTS="a b c"` on the
  caddy service env if the lab moves to a different LAN IP. The
  `default_sni` value would also need updating in that scenario.
  → **Superseded 2026-05-29: auto-detected, no hardcoding. See below.**

## 2026-05-29 — network portability (auto-detect LAN IP)

### Problem

The Caddyfile pinned the LAN IP in two places (`default_sni` and the
host list). Anyone cloning the project on a different network — i.e.
every learner — got a blank admin portal: their browser hit
`https://<their-ip>/`, Caddy had no cert for that IP, served the
`192.168.1.98` default cert (SAN mismatch) and an empty 200 body.
Observed directly: `curl -ks https://<new-ip>/admin/login` →
`http_code=200 body_bytes=0`, while `https://localhost` → `2044`.

### Decision

Remove all hardcoded IPs. The only network-dependent value is the
host's LAN IP; inject it via two env vars and auto-detect it at launch.
Alternatives considered and rejected: on-demand TLS (can't cover the
no-SNI laptop browser hitting an IP literal — still needs a default
cert), and `nip.io`/`sslip.io` hostnames (needs public DNS — wrong for
an air-gapped training LAN). See `references/tls-strategy.md`
§"Network portability".

### Changes

- `output/Caddyfile`: `default_sni {$VULNMNO_DEFAULT_SNI:localhost}`
  and host list `{$VULNMNO_TLS_HOSTS:localhost 127.0.0.1 10.0.2.2}`.
  Fallbacks are network-independent, so a bare `docker compose
  --profile tls up` still works anywhere (same-machine + emulator).
- `output/docker-compose.yml`: caddy `environment:` passes both vars
  with `${VAR:-fallback}` defaults.
- `output/scripts/up.sh` (new): detects the LAN IP as the source
  address of the default route (`ip route get 1.1.1.1`, which inherently
  skips docker bridges), adds any extra non-bridge interface IPs,
  degrades to `localhost` when air-gapped, writes `docker/.env`, and
  brings the stack up with `--profile tls`. **VPN-aware**: if the
  default route is a tunnel (`tun*/tap*/wg*/ppp*` — common for the
  pentest audience on HTB/THM), it uses a physical-interface IP for the
  cert instead of the VPN address. Accepts an explicit override
  (`up.sh <ip>`) for macOS/WSL2 or when the guess is wrong.
- `output/.env.example` (new) + `docker/.gitignore`: `.env` holds the
  detected IP and is gitignored, so the next clone can't inherit a
  stale IP. `.env.example` ships as the template.

### Verification (network 172.16.206.207, no value typed anywhere)

```
$ bash src/scripts/up.sh
Detected LAN IP : 172.16.206.207
TLS host list   : 172.16.206.207 10.0.2.2 localhost 127.0.0.1
Default SNI cert: 172.16.206.207

# cert served with NO SNI (laptop browser hitting the IP literal):
openssl s_client -connect 172.16.206.207:443   → SAN: IP 172.16.206.207   ✔ (was 192.168.1.98)
curl -ks https://172.16.206.207/admin/login     → 200, body=2044           ✔ (was body=0)

# no regression on the constant-address clients:
SNI=10.0.2.2 (emulator)   → SAN: IP 10.0.2.2,  body=2044   ✔
https://localhost          → body=2044                      ✔
http://172.16.206.207/…    → 308 → https://…                ✔

# .env correctly classified by git:
.env         → !! (ignored)
.env.example → ?? (tracked)

# explicit-override path end-to-end (arg → .env → compose → Caddy → SAN):
bash up.sh 10.9.9.9   → default_sni=10.9.9.9, host list prepends 10.9.9.9
openssl s_client -servername 10.9.9.9  → SAN: IP 10.9.9.9   ✔
bash up.sh            → restored SAN: IP 172.16.206.207      ✔

# branch logic (isolated): normal→default-route src; tun0/wg0→physical IP
# (NOT the VPN address); override→forced value.
```

### Status: PASS

Cert SAN now matches the auto-detected IP with zero hardcoding. The
solution is verified on one network; by construction the only variable
input is the default-route source IP, so it generalises to any LAN.
Re-run `up.sh` after a network change.

## 2026-05-29 — enable Burp/MITM interception of the app's HTTPS

### Problem

Intercepting the Android app through Burp failed (app showed "Network
error") even with Burp's CA trusted on the device and the app trusting
user CAs. The browser worked. Root cause, proven by inspecting the leaf
Burp presents:

```
app target = 172.16.206.207:443  (an IP literal)
Burp leaf SAN  : DNS:172.16.206.207        (DNS-type entry, CN empty)
Caddy real SAN : IP Address:172.16.206.207 (iPAddress entry)
```

OkHttp's hostname verifier requires an **iPAddress** SAN when the target
is an IP literal; Burp only emits a **DNS**-type SAN for it (and has no
toggle to change that), so OkHttp raises `SSLPeerUnverifiedException`.
curl/browsers are lenient (and browsers only ever hit hostnames), which
is why only the app broke.

### Fix

Give the app a **hostname** to connect to so Burp's DNS-type SAN matches.
`up.sh` now derives `<primary-ip>.nip.io` (public wildcard DNS → the IP)
and adds it to `VULNMNO_TLS_HOSTS`, so Caddy issues a cert for it and
routes it. The trainee points the app's backend override at that name
while proxying; with the proxy on, Burp (not the phone) resolves nip.io.

### Verification (network 172.16.206.207)

```
host list now: 172.16.206.207 172.16.206.207.nip.io 10.0.2.2 localhost 127.0.0.1
Caddy direct,  Host=…nip.io           → 200, 2044
app→Burp→Caddy, https://…nip.io/…     → 200, 2044
Burp leaf for …nip.io: SAN DNS:172.16.206.207.nip.io  → matches host → OkHttp accepts
```

### Status: PASS (laptop-side chain). The app-side login through Burp is
the trainee's final confirmation; the cert it will be offered is verified
to carry a matching DNS SAN.
