# Stage 15 — Operator quickstart

This stage adds a Caddy reverse-proxy so the admin portal works over
HTTPS. The backend itself does not change — Caddy terminates TLS and
forwards plain HTTP to `backend:8000` inside the Docker network.

## Bring it up

```bash
cd src/docker
docker compose --profile tls up -d
```

The `tls` profile activates the `caddy` service. Without it,
`docker compose up` behaves exactly as before (no proxy, no TLS).

## Verify

```bash
# Cert is locally-signed; -k skips the trust check.
curl -k -sS -o /dev/null -w '%{http_code}\n' https://<host>/admin/login
# → 200

# HTTP redirects to HTTPS:
curl -sS -o /dev/null -w '%{http_code} -> %{redirect_url}\n' http://<host>/admin/login
# → 308 -> https://<host>/admin/login

# Full login round-trip:
BASE=https://<host>
curl -k -sS -c /tmp/jar -o /tmp/login.html "$BASE/admin/login"
CSRF=$(grep -oP 'name="csrf_token" value="\K[^"]+' /tmp/login.html)
curl -k -sS -b /tmp/jar -c /tmp/jar -X POST "$BASE/admin/login" \
    --data-urlencode "username=ops" \
    --data-urlencode "password=admin1234" \
    --data-urlencode "csrf_token=$CSRF" \
    -o /dev/null -w '%{http_code} -> %{redirect_url}\n'
# → 303 -> /admin/
curl -k -sS -b /tmp/jar "$BASE/admin/" -o /dev/null -w '%{http_code}\n'
# → 200
```

Over HTTPS the cookie jar mechanism works again because the `Secure`
flag is finally satisfied.

## Trust the local CA (optional, removes the browser warning)

```bash
bash stages/15_tls_termination/output/scripts/install_caddy_ca.sh ./caddy-root.crt
# then follow the per-platform import steps printed by the script,
# or read references/trust-onboarding.md for the full menu.
```

## Tear down

```bash
docker compose --profile tls down
```

The backend, db, and provisioning-mock services keep running unless you
explicitly `down` them too. To wipe the local CA (forces fresh keys on
next start, invalidates all previously-trusted leaf certs):

```bash
docker compose --profile tls down
docker volume rm src_caddy_data src_caddy_config
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `bind: address already in use` on :80 or :443 | Another service on the host owns the port | `sudo lsof -i :443`; either stop the other process or remap the Caddy ports in compose (e.g. `8443:443`) |
| Browser still on the HTTP login page after redirect loop | Browser cached the previous HTTP response | Force-reload (Shift+Reload) or clear cookies for that host |
| `curl: (60) SSL certificate problem` and you've imported the CA | curl on Debian/Ubuntu uses `/etc/ssl/certs/ca-certificates.crt`; missed an `update-ca-certificates` step | Re-run `sudo update-ca-certificates`; if that fails, use `--cacert ./caddy-root.crt` to point curl at the cert directly |
| Admin login redirects to `/admin/login` instead of `/admin/` | The session cookie isn't surviving the POST — usually because you mixed HTTP and HTTPS during the round-trip | Make sure every step (GET, POST, follow-up GET) uses `https://` |
| "502 Bad Gateway" from Caddy | The `backend` container isn't up or is unhealthy | `docker compose ps`; check `docker compose logs backend` |

## What this stage does not change

- The mobile app's traffic. Android keeps using `http://<host>:8000` for
  the JSON API. The runtime BaseURL override added in Phase 1 supports
  HTTPS too, but TLS for the API surface is out of scope here.
- The backend listening port. `backend:8000` is still published as
  `8000:8000`, so direct API access from the LAN keeps working.
- Any application code. The same `SessionMiddleware(https_only=...)`
  rule from `app/main.py` is now satisfied by the proxy hop.
