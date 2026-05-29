# VulnMNO Build Workspace — Layer 1 (Routing)

This file routes a task to the right stage. Read [CLAUDE.md](CLAUDE.md) first if you have not.

## Pipeline overview

```
docs/VulnMNO.md
      │
      ▼
01_requirements ─► 02_api_contract ─► 03_data_model ─► 04_api_build ─┐
                          │                                            │
                          └────────────► 05_mobile_design ─► 06_mobile_build ─► 07_integration
```

Stage 02 (API contract) is the workspace's central artifact: it is consumed by both the backend track (03 → 04) and the mobile track (05 → 06). Stage 07 integrates and validates end-to-end.

## Stage routing

| If the task is… | Go to |
| --- | --- |
| "Define the phase-1 backlog and trace journeys → endpoints → entities" | [stages/01_requirements/CONTEXT.md](stages/01_requirements/CONTEXT.md) |
| "Author the OpenAPI 3.1 contract (auth, errors, schemas, endpoints)" | [stages/02_api_contract/CONTEXT.md](stages/02_api_contract/CONTEXT.md) |
| "Design SQLAlchemy models, Alembic migrations, seed data" | [stages/03_data_model/CONTEXT.md](stages/03_data_model/CONTEXT.md) |
| "Implement the FastAPI backend" | [stages/04_api_build/CONTEXT.md](stages/04_api_build/CONTEXT.md) |
| "Design Android screens, navigation, and state" | [stages/05_mobile_design/CONTEXT.md](stages/05_mobile_design/CONTEXT.md) |
| "Implement the Android Compose app" | [stages/06_mobile_build/CONTEXT.md](stages/06_mobile_build/CONTEXT.md) |
| "Wire app to API, run end-to-end, write README" | [stages/07_integration/CONTEXT.md](stages/07_integration/CONTEXT.md) |
| "Adjust code style, naming, or run instructions" | [_config/CONTEXT.md](_config/CONTEXT.md) |
| "Look up a component, role, entity or endpoint" | [shared/glossary.md](shared/glossary.md) |
| "Set phase, ports, DB choice, build variants" | [setup/questionnaire.md](setup/questionnaire.md) |

## Top-level READMEs — two audiences

Two README files exist on purpose. Keep their scopes distinct and edit each at its own altitude.

| File | Audience | Scope |
| --- | --- | --- |
| [README.md](README.md) | **Repo visitor on GitHub** — this is the landing page that renders on the project's GitHub front page. | Full overview: what VulnMNO is, phases 1–2 + lab hardening, workspace layout, quickstart, seed creds, the **training-lab vulnerability surface (M1/M3)**, gateway-driver matrix, troubleshooting table, and the MWP methodology one-pager. The first and most complete thing anyone reads. |
| [src/README.md](src/README.md) | **Someone who just wants to run the lab.** | Short, practical operator steps only: start the stack (`up.sh`), trust the CA, build/install the Android app, Burp MITM, smoke checks, DB access. No project background, no phase history, no methodology. |

When a change touches both (e.g. a new launch flag or workflow), put the **full context** in the root `README.md` and only the **bare practical step** in `src/README.md`. Don't let `src/README.md` grow into a second overview.

## Shared resources (Layer 3, used across stages)

- [_config/tech-stack.md](_config/tech-stack.md) — locked dependency versions and stack decisions.
- [_config/conventions.md](_config/conventions.md) — file naming, IDs (`REQ-`, `EP-`, `ENT-`, `SCR-`), table shapes.
- [_config/code-style.md](_config/code-style.md) — Python and Kotlin style rules.
- [shared/glossary.md](shared/glossary.md) — canonical names for components, roles, entities and endpoint groups.
- [shared/source-pointer.md](shared/source-pointer.md) — section-level pointers into `docs/VulnMNO.md`.

## What never to load

Do not load all stages' references at once. Each stage's `## Inputs` table names exactly what to read. Loading everything reproduces the monolithic-prompt problem MWP is designed to avoid (`docs/MWP.md` §3.2).

## Cross-track sync rule

If a downstream stage (03, 04, 05 or 06) discovers that the OpenAPI spec in `stages/02_api_contract/output/` is wrong or incomplete, **do not patch in the downstream stage**. Fix stage 02 first, re-export the spec, then continue. This preserves the single-source-of-truth property of the contract.
