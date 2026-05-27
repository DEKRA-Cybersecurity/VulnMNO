# Conventions

## File naming

- Stage outputs use kebab-case: `endpoints.md`, `data-model.md`, `screens.md`.
- Code lives in stage outputs:
  - Backend: `stages/04_api_build/output/backend/`
  - Android: `stages/06_mobile_build/output/android/`
- Never modify `docs/`. Derived artifacts always go to `stages/*/output/`.

## ID prefixes

Every traceable item gets a stable ID. Downstream stages cite IDs, never paraphrases.

| Prefix | Meaning | Owning stage |
| --- | --- | --- |
| `REQ-` | Requirement (journey, story, acceptance criterion) | 01 |
| `EP-` | API endpoint contract | 02 |
| `ENT-` | Domain entity / DB table | 03 |
| `SCR-` | Mobile screen | 05 |
| `NAV-` | Navigation transition between screens | 05 |
| `INT-` | Integration / end-to-end test case | 07 |
| `ADM-` | Admin portal screen (Phase 2) | 11 |
| `AEP-` | Admin portal HTML endpoint (Phase 2) | 09 |
| `GW-` | External gateway operation (payment / provisioning / push) | 09 |
| `LOY-` | Loyalty engine rule | 08 |

IDs are zero-padded to three digits within their prefix: `REQ-007`, `EP-012`, `SCR-004`, `ADM-005`, `AEP-014`. IDs are immutable once assigned — never renumber. Phase 2 requirements start at `REQ-200`.

## Markdown table shapes

**Requirements (stage 01 `backlog.md`):**

| ID | Journey (§9.x) | Actor | Story | Acceptance criteria | Related EP- / ENT- |
| --- | --- | --- | --- | --- | --- |

**Endpoints (stage 02 `endpoints.md`):**

| ID | Method | Path | Auth | Request schema | Response schema | Errors | Journey (§9.x) |
| --- | --- | --- | --- | --- | --- | --- | --- |

**Entities (stage 03 `entities.md`):**

| ID | Table | Columns | PK / FK | Indexes | Source (§11) |
| --- | --- | --- | --- | --- | --- |

**Screens (stage 05 `screens.md`):**

| ID | Name | Journey (§9.x) | Reads (EP-) | Writes (EP-) | State | Navigation in / out |
| --- | --- | --- | --- | --- | --- | --- |

**Integration tests (stage 07 `e2e-cases.md`):**

| ID | Journey | Steps (SCR- + EP-) | Expected | Seed data |
| --- | --- | --- | --- | --- |

## Code conventions

- Module / package names: snake_case (Python), lowercase (Kotlin packages).
- Pydantic models named `XxxRead`, `XxxCreate`, `XxxUpdate` — never bare `Xxx`.
- DTOs on the Android side use the `XxxDto` suffix and live in a `data.remote.dto` package.
- One FastAPI router per endpoint group from §12 (auth, customers, accounts, shop, plans, usage, support, notifications).

## Commit traceability

When code lands in stage 04 or 06, the commit message should cite the `EP-` and `REQ-` IDs it implements. Example: `EP-014, REQ-021: shop/purchases POST with promo`.
