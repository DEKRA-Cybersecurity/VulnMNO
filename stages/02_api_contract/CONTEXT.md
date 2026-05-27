# Stage 02 — API contract (OpenAPI 3.1)

Produce the **single source of truth** for the VulnMNO HTTP API. The output of this stage is consumed by both the backend track (03 → 04) and the mobile track (05 → 06). When the contract changes, this stage changes first.

## Inputs

**Layer 4 (working):**
- `../01_requirements/output/backlog.md`
- `../01_requirements/output/traceability.md`

**Layer 3 (reference):**
- `references/contract-rules.md` — auth, errors, pagination, naming, versioning rules.
- `../../shared/glossary.md` — endpoint groups and entity names.
- `../../shared/source-pointer.md` — §12 (endpoint list), §13 (payload shapes).
- `../../_config/conventions.md` — `EP-` IDs and `endpoints.md` table shape.
- `../../_config/tech-stack.md` — locked stack (OpenAPI 3.1, OAuth2 + JWT).

Do **not** load `docs/VulnMNO.md` directly except for §12 and §13 spot-checks via `source-pointer.md`. Everything else has been distilled by stage 01.

## Process

1. Walk `traceability.md`. For each candidate §12 endpoint, draft an `EP-…` row: method, path, auth requirement, request schema name, response schema name, error codes, journey.
2. Define the auth model exactly once in `contract-rules.md` terms: OAuth2 password flow + JWT bearer, refresh endpoint, OTP challenge response shape.
3. Define the single error envelope and the master `error.code` enum. Every error response in every endpoint uses this envelope.
4. Define schemas for every §11 entity that crosses the wire, named `XxxRead`, `XxxCreate`, `XxxUpdate`. Match `docs/VulnMNO.md` §13 example payloads field-for-field (names, types, formats).
5. Define pagination: cursor or page+size? Pick one consistent style (see `contract-rules.md`) and apply to every list endpoint.
6. Write the OpenAPI 3.1 YAML by hand (or generate it from a Python stub in `output/` — see `contract-rules.md`). Validate it with `openapi-spec-validator` before committing.
7. Resolve every Open question recorded by stage 01. Each resolution is logged at the bottom of `endpoints.md`.

## Outputs

Write to `output/`:

- `endpoints.md` — table per the `Endpoints` shape in `_config/conventions.md`, sorted by endpoint group then path. One row per `EP-…`.
- `openapi.yaml` — OpenAPI 3.1 spec. Single file. All schemas inline under `components.schemas`. Tagged by endpoint group from the glossary.
- `error-codes.md` — the master `error.code` enum, one row per code, with which `EP-…` raises it.
- `auth-model.md` — JWT shape (`sub`, `exp`, `iat`, `jti`), OTP challenge flow, refresh flow, token TTLs decided here.

All four files open with the four-section header (Scope / Inputs / Findings / Open questions).
