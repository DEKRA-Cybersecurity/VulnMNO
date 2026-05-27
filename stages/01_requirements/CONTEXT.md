# Stage 01 — Requirements & scope

Turn the prose product description in `docs/VulnMNO.md` into a structured, traceable backlog: requirements (`REQ-`) → journeys (§9.x) → candidate endpoints (§12 references) → candidate entities (§11 references).

This stage produces *facts about what to build*, not design decisions. The OpenAPI spec, the DB schema and the screen list come later.

## Inputs

**Layer 4 (working):**
- `../../docs/VulnMNO.md` — canonical product source (§2, §4, §7.1, §9.1–§9.6, §10, §11, §12).
- `../../setup/questionnaire.md` — phase scope confirmation.

**Layer 3 (reference):**
- `../../shared/glossary.md` — canonical component, role, entity and endpoint-group names.
- `../../shared/source-pointer.md` — section index.
- `../../_config/conventions.md` — `REQ-` prefix and `backlog.md` table shape.
- `references/requirements-template.md` — the structure for each `REQ-`.

## Process

1. For each journey §9.1–§9.6, write a top-level section (`## §9.1 Login`, …).
2. Inside each journey, expand the steps from the source into atomic `REQ-…` items, one per acceptance criterion. Use the journey's own steps as the skeleton — do not invent new steps.
3. For each `REQ-`, name the candidate endpoint(s) from §12 (by HTTP method + path) and the candidate entities from §11 (by name). Use *candidates* — stage 02 may rename or split them, but stage 01 records the source pointers.
4. Capture cross-cutting requirements separately under `## Cross-cutting`: authentication & session model (per §13.1), error envelope, pagination, currency / datetime / ID format, audit logging (§7.14).
5. Mark out-of-phase items explicitly with `OUT-OF-PHASE-1` and a one-line justification (e.g. push delivery, admin portal).

## Outputs

Write to `output/`:

- `backlog.md` — single document, organized by journey, each row following the `Requirements` shape in `_config/conventions.md`:

  ```
  | ID | Journey (§9.x) | Actor | Story | Acceptance criteria | Related EP- / ENT- |
  ```

  Opens with the four-section header (Scope / Inputs consumed / Findings / Open questions).

- `traceability.md` — a single matrix table with one row per `REQ-`: `REQ-ID | Journey | §12 endpoint(s) | §11 entities`. Stage 02 uses this as its work input.
