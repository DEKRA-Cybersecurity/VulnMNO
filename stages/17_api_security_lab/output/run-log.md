# Stage 17 — run log

Date: 2026-09-11. Two passes recorded below: an initial documentation-only
survey, then an implementation + live-verification pass that closed out the
six "planned" categories. Every claim is backed by a direct read of the file
cited or a captured command transcript — nothing inferred without checking.

## Pass 1 — documentation-only survey

## Endpoints enumerated

- `app/routers/{accounts,auth,customers,loyalty,notifications,plans,shop,support,usage}.py`
- `app/admin/routers/{admin_users,audit,auth,customers,dashboard,plans,promotions,refunds,reports,tickets}.py`

## Classification evidence

| Category | Status | Evidence checked |
|---|---|---|
| API1 BOLA | Planned | `accounts.py:171-177` (`Invoice.account_id == acct.id`), `support.py:177-183` (`SupportTicket.customer_id == customer.id`) — both correctly scoped today |
| API2 Broken Auth | Live | `services/auth.py:94-104` (attempts-cap-removed comment), `routers/auth.py:32-97` (only `/login` carries `@limiter.limit`) |
| API3 Mass assignment | Planned | `schemas/customer.py:31-34` (`ContactDetailsUpdate` — no writable role/tier field), `routers/customers.py:55-63` (explicit per-field checks, not a raw `setattr` loop) |
| API4 Resource consumption | Live | `routers/auth.py:66-71` (`/refresh`, no limiter), `routers/usage.py:89-150` (sibling list endpoints all `Query(20, ge=1, le=100)`; `export_usage` has neither `limit` nor `@limiter.limit`) |
| API5 Function-level authz | Planned | `admin/routers/refunds.py:21-93`, `admin_users.py:23-93` — every route behind `Depends(require_module(...))` |
| API6 Business-flow abuse | Live | `routers/shop.py:184-190` (`coupon.usage_count += 1`, global), `services/shop.py:34` (`usage_count >= usage_limit` check, not per-customer), `seed.py:202-234` (`SUMMER20` has no `max_prior_purchases` rule; `usage_limit=10000`) |
| API7 SSRF | Planned | `gateways/provisioning.py:46-77`, `config.py:50-51` (`VULNMNO_PROVISIONING_URL` is server config, never per-request input) |
| API8 Security misconfig | Live | `main.py::create_app` — `FastAPI(...)` with no `docs_url`/`redoc_url`/`openapi_url` override; root `README.md` already labels `/docs` "(unauth)" |
| API9 Inventory | Planned | No shadow endpoint found in `app/routers/` or `app/admin/routers/` — would need to be added |
| API10 Unsafe consumption | Planned | `gateways/provisioning.py:63-77`, `gateways/payment.py:116-144` (`r.json().get(...)`, no schema validation) — reachable only if `provisioning_driver=http` / `payment_driver=stripe` (both default `dev`, `config.py:46,50`) |

## Outputs produced in Pass 1

- `stages/17_api_security_lab/CONTEXT.md`
- `stages/17_api_security_lab/references/owasp-api-top10-mapping.md`
- Ten guides in `src/docs/vulns/api/` — API2/4/6/8 bannered live, API1/3/5/7/9/10 bannered "planned, not yet implemented"
- `README.md` — Training-lab surface section extended with a Live/Planned split

## Pass 2 — implementation + live verification

Applied one deliberate diff per remaining category to `src/backend`
(each adds new surface — a new endpoint or a new schema field — rather than
weakening an existing correct check):

| Category | File(s) changed | What was added |
|---|---|---|
| API1 | `app/routers/support.py` | `get_ticket_by_reference` — same `SupportTicket` lookup as `_load_ticket_full`, minus the `customer_id` filter |
| API3 | `app/schemas/customer.py`, `app/routers/customers.py` | `ContactDetailsUpdate.loyaltyTier` field + unguarded write in `update_contact_details` |
| API5 | `app/admin/routers/refunds.py` | `refund_quick_approve` — same approval logic as `refund_approve`, gated by `get_current_admin` instead of `require_module(...)` |
| API7 | `app/schemas/auth.py`, `app/routers/auth.py` | `DeviceRegisterRequest.callbackUrl` + an unrestricted `httpx.get(callbackUrl)` in `register_device` |
| API9 | `app/routers/customers.py` | `debug_dump_customer` — unauthenticated, dumps every raw `Customer` column |
| API10 | `app/routers/shop.py` | `provisioning_callback` — unauthenticated webhook that trusts `{"purchaseId","status"}` and can trigger a wallet credit |

### Live verification (throwaway instance, then torn down)

Environment: `docker run python:3.12-slim`, backend deps installed directly
(no editable install — the repo's `pyproject.toml` flat-layout triggers a
setuptools "multiple top-level packages" error for `pip install -e .`; ran
`uvicorn` with `PYTHONPATH=/app` instead, dependencies unpinned beyond the
version floors already in `pyproject.toml`), `VULNMNO_ENV=dev`, SQLite dev DB,
seed data auto-applied, port `18000→8000`. Torn down with `docker rm -f`
afterward; the generated `dev.db` was deleted (SQLite dev artifact, not
meant to persist from a throwaway run).

Every one of the ten guides' "Verified exploitation" sections was run for
real against this instance — full transcripts live in each guide, not
duplicated here. Summary of what was proven:

- **API1** — customer3 read customer1's ticket via `/by-reference/`, 200 with
  real content; the normal endpoint correctly 404s for the same request.
- **API3** — `CUST-10003.loyaltyTier` flipped `bronze → platinum` via a plain
  contact-details PUT, confirmed persisted on re-read.
- **API5** — `support_agent` (no `REFUND_WORKFLOW` grant) got `403` from the
  real `/approve` route, then `303` (success) from `/quick-approve`; a
  `billing` session confirmed the refund shows `approved`.
- **API7** — a registered device's `callbackUrl` caused the backend's own
  access log to show a `127.0.0.1`-origin request to the target path —
  proof the server (not the client) made the fetch.
- **API9** — unauthenticated `GET /_debug/{id}` returned the real Argon2
  password hash; path confirmed present in `/openapi.json`.
- **API10** — an unauthenticated webhook call with a guessed `purchaseId`
  credited `4.99 EUR` back to a wallet with no legitimate provisioning
  failure.

## Outputs produced in Pass 2

- Code changes listed in the table above (also listed in `CONTEXT.md`'s
  `## Outputs`).
- All ten guides under `src/docs/vulns/api/` rewritten to "Status: live —
  implemented and verified," each with a real captured transcript replacing
  the earlier hypothetical "once introduced" framing.
- `stages/17_api_security_lab/references/owasp-api-top10-mapping.md` —
  rewritten: single live table + verification summary (superseded the
  Live/Planned split from Pass 1).
- `stages/17_api_security_lab/CONTEXT.md` — rewritten to describe both
  passes and the final all-live state.
- `README.md` — Training-lab surface API section rewritten to a flat list
  (all ten live, no more Planned column).

## Not done

- CI enforcement (an openapi-diff gate for API9, a webhook-signature test for
  API10) — flagged as a follow-up in the mapping doc, not built.
- No decision made on whether the six newly-introduced labs should ship
  disabled-by-default behind a feature flag for non-training deployments.
