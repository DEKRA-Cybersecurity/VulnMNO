# TLS strategy — Caddy + `tls internal`

## Decision

Terminate TLS at a **Caddy 2** reverse-proxy container that sits in front
of the existing `backend` service, using Caddy's built-in `tls internal`
directive. Caddy generates a local CA on first boot and issues a leaf
certificate covering whatever host name / IP the operator hits. The
backend itself keeps listening on plain HTTP (`:8000`) inside the Docker
network.

## Why not …

| Option | Why rejected |
| --- | --- |
| **uvicorn `--ssl-certfile` / `--ssl-keyfile` directly** | Couples cert lifecycle to the app container. Requires baking cert paths into the backend Dockerfile or mounting secrets. No HTTP→HTTPS redirect; uvicorn can only listen on one port. Harder to regenerate certs without restarting the whole app. |
| **nginx + manually-generated self-signed cert** | More moving parts (cert generation script, separate config). No automatic regeneration. The auto-trust trick (`tls internal`) doesn't exist; every workstation has to import a manually-crafted root. |
| **Traefik** | Overkill for one upstream service. Its config model is service-discovery driven and pulls labels off other containers — more surface area than we need for a one-shot reverse-proxy. |
| **mkcert on the host, mount cert into the container** | Works but requires the host to have mkcert installed and the operator to remember to regenerate certs when the LAN IP changes. Caddy `tls internal` handles cert regeneration automatically (and per-IP). |
| **Caddy with a public ACME issuer (Let's Encrypt)** | Wrong tool for a private LAN training stack. The IP isn't publicly reachable and we'd be flagging certificate-transparency logs with a synthetic name. |

## Why `tls internal` specifically

- **Zero-config cert issuance.** First request triggers cert generation
  for the requested SNI / IP. Subsequent requests reuse the cached cert.
- **IP literals supported.** Unlike public ACME, Caddy's internal issuer
  signs certs for raw IPs (192.168.x.x). The training lab connects by IP,
  not DNS.
- **Persistent CA.** The local CA's root key is stored under
  `/data/caddy/pki/authorities/local/` — by mounting that path on a named
  volume we keep the CA stable across container restarts. Operators
  import the root cert once; subsequent leaf certs (when the LAN IP
  changes) chain back to the same root and remain trusted.
- **HTTP→HTTPS redirect comes for free.** The `:80` block ships with the
  same compose service.

## Network portability (no hardcoded IPs)

The lab is cloned by many learners on many networks, so the Caddyfile must
carry **zero** static IPs. The insight: the *only* value that changes per
network is the host's LAN IP. Everything else is constant —
`10.0.2.2` (the Android emulator's view of the host loopback), `localhost`,
`127.0.0.1`. So we externalise just that one value into two env vars:

| Var | Used for | Who needs it |
| --- | --- | --- |
| `VULNMNO_TLS_HOSTS` | hosts `tls internal` pre-issues certs for | a physical phone / LAN peer (sends SNI = the LAN IP) |
| `VULNMNO_DEFAULT_SNI` | cert served when the client sends no SNI | the laptop browser / curl hitting an IP literal (RFC 6066 — no SNI for IPs) |

Both have network-independent fallbacks baked into the Caddyfile
(`{$VULNMNO_DEFAULT_SNI:localhost}` and `{$VULNMNO_TLS_HOSTS:localhost
127.0.0.1 10.0.2.2}`), so a bare `docker compose --profile tls up` works on
any machine for same-machine + emulator access with no setup at all.

`scripts/up.sh` fills in the LAN IP automatically: it reads the source
address of the default route (`ip route get 1.1.1.1`), which is the
interface that actually reaches off-box and **inherently excludes docker
bridges** (they aren't on the default route — a plain `ip addr` sweep would
wrongly pick up the `172.x.0.1` bridge gateways). It writes `docker/.env`,
which Compose interpolates into the caddy service env. `.env` is gitignored
so a clone can't inherit someone else's IP; `.env.example` ships as the
template.

### Why not the alternatives

| Option | Why rejected |
| --- | --- |
| **On-demand TLS** (`tls internal { on_demand }`) | Issues a cert for whatever SNI arrives — great for the phone/emulator, but the laptop browser hitting `https://<ip>` sends **no** SNI, so on-demand never triggers for it and you *still* need a correct `default_sni`. It removes host-list maintenance that auto-detect already handles for free, at the cost of an `ask`-endpoint config whose necessity is Caddy-version-dependent. Not worth it for v1. |
| **`nip.io` / `sslip.io` wildcard DNS** (`https://<ip>.sslip.io`) | A real hostname, so the browser *does* send SNI and on-demand could issue automatically — but it depends on a **public DNS resolver**, which a fully isolated / air-gapped pentest lab won't have. The IP is still embedded in the URL anyway. |
| **mDNS `vulnmno.local`** | Flaky across OSes and routinely blocked on corporate/guest networks. Not dependable for "anyone, any network". |
| **Keep editing the Caddyfile by hand** | The status quo we're replacing — not portable, and the exact cause of the blank-portal report. |

The chosen approach is the only one that is self-contained (no internet),
deterministic, and one-command.

## Trust model

There is no chain to a public root. The Caddy local CA is exactly that —
**local**. Operators have three options:

1. **Accept the warning once per browser session.** Fine for ad-hoc
   inspection during the lab.
2. **Import the Caddy root CA into the workstation trust store.** Removes
   the warning permanently. The extraction helper at
   `output/scripts/install_caddy_ca.sh` pulls
   `/data/caddy/pki/authorities/local/root.crt` out of the running
   container; the user imports it via their OS or browser tooling. Steps
   for common platforms are in `trust-onboarding.md`.
3. **Ignore TLS entirely and use HTTP.** Possible for the API surface
   (`/api/*` — JWT auth, no `Secure` cookie) but breaks the admin portal
   by design (that's the whole reason this stage exists).

## Why the backend doesn't change

`app/main.py` already sets `https_only=settings.env != "dev"`. With
`VULNMNO_ENV=prod-like` (the value used in `src/docker/docker-compose.yml`)
the session cookie is already emitted with `Secure`. The problem was
**reachability**, not configuration: browsers were dropping the cookie
because the page came over HTTP. Terminating TLS in front of the backend
fixes that without touching app code.

The proxy forwards `X-Forwarded-Proto: https` so any future code that
needs to know the original scheme (e.g. building absolute redirect URLs)
sees the correct value. Uvicorn must be started with `--proxy-headers` to
honour those forwarded headers; that flag is already part of the
`uvicorn[standard]` defaults in the existing Dockerfile when running
behind a known proxy chain.

## Failure modes & remedies

| Symptom | Cause | Remedy |
| --- | --- | --- |
| Browser shows "NET::ERR_CERT_AUTHORITY_INVALID" | Caddy root CA not imported into the trust store | Either accept the exception or run `install_caddy_ca.sh` and import the resulting `.crt` |
| `curl: (60) SSL certificate problem: self signed certificate` | Same | `curl -k …` or `curl --cacert caddy-root.crt …` |
| Admin login still 400 with "Session expired" after going HTTPS | You're still hitting `http://…/admin/login`. The cookie issued over HTTP doesn't ride back on the HTTPS POST | Confirm the URL bar shows `https://` and the cookie jar has `vulnmno_admin_session` with `Secure` flag |
| Caddy container restarts on boot | Port 80 or 443 already taken on the host | `sudo lsof -i :443` and free the port, or remap `caddy` to `8443:443` and use `https://<host>:8443` |
| Cert regenerates every restart and trust is lost | `caddy_data` volume not declared / not persistent | Verify `docker volume ls` shows `*_caddy_data` and that the compose file declares it under top-level `volumes:` |
