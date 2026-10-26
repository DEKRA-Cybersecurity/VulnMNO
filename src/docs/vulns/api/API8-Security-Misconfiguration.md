# API8 — Security Misconfiguration · VulnMNO Pentest Guide

This guide documents a **pre-existing** API8 weakness in the VulnMNO backend.
No code is added for this lab — it is already present (and already
acknowledged in the root `README.md`) and catalogued here so trainees can
practise locating, exploiting and remediating it.

> **Scope.** Backend only, pure HTTP, **no authentication needed at all** —
> that's the point.

OWASP API Security reference: **API8:2023 — Security Misconfiguration.**

| Lab | Subcategory | Severity | Difficulty |
|---|---|---|---|
| L1 | Unauthenticated Swagger UI + full OpenAPI schema | Medium | Easy |

## Where it lives

- `GET /docs` — Swagger UI
- `GET /redoc` — ReDoc UI
- `GET /openapi.json` — the full machine-readable schema
- **Code:** `app/main.py::create_app` —
  `FastAPI(title="VulnMNO API", version="0.2.0-phase2", lifespan=lifespan)`,
  with no `docs_url=None` / `redoc_url=None` / `openapi_url=None` override and
  no auth dependency mounted in front of any of the three.

## Why it is API8

FastAPI serves `/docs`, `/redoc` and `/openapi.json` by default unless the
app explicitly disables or protects them. VulnMNO never does either. The
root `README.md`'s own URL table even names this outright:

```
| `http://<host>:8000/docs`  | OpenAPI / Swagger (unauth) |
```

That's honest documentation of the current (mis)configuration, not a
mitigation. Anyone who can reach the API port — no `Authorization` header,
no cookie, nothing — gets:

- Every route, method, path/query/body parameter, and response shape in the
  system (customer **and** admin surface), including fields never rendered
  in any client UI.
- Every Pydantic schema (`ContactDetailsUpdate`, `RefundRequest`, admin
  payloads, …), which turns "find the interesting fields" for API1/API3/API5
  reconnaissance into "read `/openapi.json`" instead of black-box guessing.
- An interactive "Try it out" console that can fire authenticated calls the
  moment an attacker obtains *any* valid token by other means.

This is the textbook API8 pattern: a default that is safe to leave on for a
closed dev environment (which is genuinely what the seed comment intends)
but was never revisited for anything resembling a production-like posture —
exactly the gap API8 exists to catch.

## How to find it (static analysis)

```bash
grep -n "FastAPI(" src/backend/app/main.py
```

No `docs_url`/`redoc_url`/`openapi_url` kwarg present → all three stay on
their defaults (`/docs`, `/redoc`, `/openapi.json`).

## Dynamic exploitation

```bash
# Full schema, zero auth
curl -s http://localhost:8000/openapi.json | python3 -m json.tool | less

# Enumerate every admin-only path straight out of the schema
curl -s http://localhost:8000/openapi.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(p) for p in d['paths'] if p.startswith('/admin')]"

# Interactive console
open http://localhost:8000/docs
```

Nothing above required a login step. Compare the surface it reveals against
`stages/02_api_contract/output/openapi.yaml` — the hand-maintained contract —
to spot any route the generated schema exposes that the contract doesn't
know about yet (a lead into API9).

## Blue-team detection

```bash
# Unauthenticated hits to the schema/docs endpoints from outside the
# expected operator IP range
grep -E "GET (/docs|/redoc|/openapi.json)" access.log \
  | awk '{print $1}' | sort | uniq -c | sort -rn
```

A spike of distinct source IPs hitting `/openapi.json` with no prior
`/api/auth/login` from the same IP is a strong recon signal.

## Remediation diff (sketch — not applied)

```diff
--- a/app/main.py
+++ b/app/main.py
@@ create_app
     app = FastAPI(
         title="VulnMNO API",
         version="0.2.0-phase2",
         lifespan=lifespan,
+        docs_url="/docs" if settings.env == "dev" else None,
+        redoc_url="/redoc" if settings.env == "dev" else None,
+        openapi_url="/openapi.json" if settings.env == "dev" else None,
     )
```

For a training lab specifically, the *intended* fix is usually "gate `/docs`
behind the same admin session auth used elsewhere" rather than removing it
outright — keeps the console useful for trainees while closing the
unauthenticated-recon gap.
