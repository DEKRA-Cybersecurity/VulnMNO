# Contract rules

Rules that bind every endpoint defined in this stage. The OpenAPI spec is the artifact, but these rules are what make it consistent.

## Versioning

- Base path is `/api`. No `/v1` prefix in phase 1 — the workspace is the version.
- Breaking changes restart stage 02 and re-export `openapi.yaml`.

## Authentication

- OAuth2 password flow with JWT bearer tokens.
- Access token: HS256, TTL 60 min, claims `sub` (customer ID, e.g. `CUST-10001`), `exp`, `iat`, `jti`.
- Refresh token: opaque random 32 bytes, base64url-encoded, stored hashed (SHA-256) server-side, TTL 30 days.
- OTP challenge: when a login attempt is for an OTP-enrolled customer, `POST /api/auth/login` returns `200` with `{ "challenge": "OTP", "challengeToken": "…" }` instead of a token pair. Client then calls `POST /api/auth/otp/verify` with the OTP and challenge token.
- OTP validity: 5 minutes (per `docs/VulnMNO.md` §13.1).
- All endpoints except `/api/auth/*` and `/api/auth/password-reset/*` require `Authorization: Bearer …`.

## Identity scoping

- `me` in any path always resolves from the access token's `sub`. Never from a path/query parameter.
- A customer can only read or write resources whose `customerId` matches their token. Cross-customer access returns `404` (not `403`) to avoid existence leaks.

## Error envelope

Every non-2xx response:

```yaml
type: object
required: [error]
properties:
  error:
    type: object
    required: [code, message]
    properties:
      code:    { type: string, description: "SCREAMING_SNAKE" }
      message: { type: string }
      details: { type: object, additionalProperties: true }
```

Master `error.code` enum is maintained in `output/error-codes.md`. Each `EP-…` lists the codes it can raise.

Standard codes (must exist):
`UNAUTHENTICATED`, `INVALID_CREDENTIALS`, `OTP_REQUIRED`, `OTP_INVALID`, `TOKEN_EXPIRED`,
`NOT_FOUND`, `VALIDATION_FAILED`, `RATE_LIMITED`, `CONFLICT`, `INTERNAL`.

Domain codes (named here, owned by their endpoint group):
`PROMO_INVALID`, `PROMO_INELIGIBLE`, `INSUFFICIENT_BALANCE`,
`PLAN_INELIGIBLE`, `PLAN_CHANGE_PENDING`,
`TICKET_CLOSED`.

## Pagination

Cursor-based on every list endpoint. Query params: `?limit=20&cursor=…`. Response shape:

```yaml
type: object
properties:
  items: { type: array }
  nextCursor: { type: string, nullable: true }
```

`limit` defaults to 20, max 100. `cursor` is an opaque base64url string.

## Naming

- Paths plural, lowercase, hyphenated: `/api/support/tickets/{ticketId}/messages`.
- Path parameter IDs match `docs/VulnMNO.md` §13 prefixed-string format (`{purchaseId}` is a string like `PUR-90001`, never an integer).
- Schema names PascalCase. Read shapes end in `Read`, create in `Create`, update in `Update`.

## Data types

- Money: `type: number`, `format: decimal`, two decimal places enforced by Pydantic at the service. Currency always EUR in phase 1.
- Datetime: `type: string`, `format: date-time`. Always UTC, suffix `Z`.
- IDs: `type: string`, with a pattern matching the §13 prefix.

## Authoring workflow

Two acceptable workflows for producing `openapi.yaml`:

1. **Hand-write the YAML** in this stage and validate with `openapi-spec-validator`. Stage 04 then mirrors the schemas in Pydantic.
2. **Stub the FastAPI app here** (a minimal `main.py` with the routers, Pydantic schemas and `pass` bodies) and export via `app.openapi()` to `output/openapi.yaml`. Stage 04 then takes the stub forward into a full implementation.

Pick one in `output/endpoints.md` (in the Findings section) and stick to it. The stub workflow is preferred because it keeps the contract and the implementation in sync from the start.
