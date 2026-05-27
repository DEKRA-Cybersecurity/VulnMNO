# Requirements template

## Shape of a `REQ-` row

```
| REQ-001 | §9.1 | Customer | As a customer, I can authenticate with phone + password and (when required) OTP to receive a session token. | Given a registered MSISDN and correct password, when I POST /api/auth/login, then I receive an access token and a refresh token. OTP challenge is returned when the customer is OTP-enrolled. | EP-001, EP-006, ENT-Customer, ENT-MobileLine |
```

Acceptance criteria use **Given / When / Then**. One row = one criterion. A user story that has three criteria becomes three `REQ-…` rows.

## Quality bar for acceptance criteria

- **Concrete payload references where possible.** "Receives an access token" is OK; "Receives a JWT with `sub=customerId`, `exp` 1h from now" is better and unambiguous for stage 04.
- **Source-grounded.** If the criterion is not derivable from `docs/VulnMNO.md`, add an **Open question** at the bottom of `backlog.md`; do not silently invent business rules.
- **Independent of design.** Do not say "the FastAPI router shall…" — that is stage 02/04 vocabulary. Say "the system shall…".

## Required cross-cutting requirements (do not omit)

| Topic | Source |
| --- | --- |
| Authentication model: phone + password, OTP for OTP-enrolled customers | §9.1, §13.1 |
| Session lifetime + refresh | §13.1 |
| Error envelope (single shape across all endpoints) | inferred — make it explicit |
| Pagination on list endpoints (purchases, transactions, usage, tickets, notifications) | inferred — make it explicit |
| Currency = EUR; money serialized as decimal with two digits | §13 examples |
| Datetime in ISO 8601 UTC | §13 examples |
| Prefixed string IDs in payloads | §13 examples |
| Audit event written for: login, purchase, plan change, refund, ticket create | §7.14, §12 events |

## OUT-OF-PHASE-1 quick list

Annotate these explicitly in `backlog.md` so stage 02 does not accidentally include them:

- §7.13 Administration portal and all admin-only endpoints.
- Real payment gateway: top-up writes a simulated transaction; do not call out.
- Real provisioning: log the intent only.
- Push delivery (FCM): `POST /api/notifications/device-token` is implemented; downstream FCM call is not.
- Refund disputes that require manual workflow — log the request only.

## Open questions block

Each requirement that requires a decision not present in the source goes under `## Open questions` in `backlog.md`. Stage 02 will resolve them; stage 01 only records them.
