# Stage 05 — Mobile design (screens, navigation, state)

Translate journeys §9.1–§9.6 and the API contract from stage 02 into a screen inventory, a navigation graph, and a per-screen state model. Stage 06 implements what stage 05 specifies.

## Inputs

**Layer 4 (working):**
- `../01_requirements/output/backlog.md`
- `../02_api_contract/output/openapi.yaml`
- `../02_api_contract/output/endpoints.md`

**Layer 3 (reference):**
- `references/screen-template.md` — shape of each `SCR-` entry.
- `../../shared/glossary.md` — reserved screen names, journey ↔ §7.1 app section mapping.
- `../../_config/conventions.md` — `SCR-` / `NAV-` IDs, `screens.md` shape.
- `../../_config/code-style.md` — Android project layout, `UiState` convention.
- `../../_config/tech-stack.md` — Compose, Hilt, Retrofit decisions.

Do **not** load the source `docs/VulnMNO.md` directly here. The screen-bearing sections (§7.1, §9.x) have been distilled into the glossary and the backlog.

## Process

1. For each reserved screen name in `shared/glossary.md`, write a `SCR-…` entry following `references/screen-template.md`.
2. Assign each screen the `EP-…` IDs it reads (typically on entry / refresh) and the `EP-…` IDs it writes (on user action).
3. Define `UiState` for each screen: `Loading`, `Content(data)`, `Error(message)`, plus screen-specific transient states (e.g. `OtpChallenge(challengeToken)` on `LoginScreen`).
4. Build the navigation graph: every screen has `Navigation in` (what brings the user here) and `Navigation out` (what destinations result from each action). Assign `NAV-…` IDs to non-trivial transitions (deep links, OTP challenge, purchase confirmation back-stack pop).
5. Decide which content lives in tabs vs separate routes. `UsageScreen` is a single route with internal tabs (calls / sms / data / roaming). `Plans` is two routes (`PlansScreen` listing + `PlanChangeScreen` confirmation).
6. Define empty / error / offline behavior per screen. Empty list endpoints should show a friendly empty state, not a spinner.
7. Specify token handling: which screens require an authenticated user, what the global auth listener does on `401` (drop tokens, navigate to `LoginScreen`, preserve deep-link target).

## Outputs

Write to `output/`:

- `screens.md` — table per `_config/conventions.md` `Screens` shape, one row per `SCR-…`, followed by a section per screen with the full `SCR-` entry from the template.
- `navigation.md` — the nav graph as a list of `NAV-…` transitions plus an ASCII tree of route hierarchy. Includes the back-stack rules for OTP, purchase confirmation, and ticket creation.
- `state-model.md` — per-screen `UiState` definitions, intended for direct translation into Kotlin sealed interfaces in stage 06.

All three files open with the four-section header (Scope / Inputs / Findings / Open questions).
