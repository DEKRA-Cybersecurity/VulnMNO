# _config — Layer 3 routing

Factory configuration for the VulnMNO build workspace. Files here are stable across runs. They define *how* code and specs are written, not *what* they say.

## Files

- [tech-stack.md](tech-stack.md) — locked stack decisions and versions (backend + mobile).
- [conventions.md](conventions.md) — file naming, ID prefixes (`REQ-`, `EP-`, `ENT-`, `SCR-`), table shapes.
- [code-style.md](code-style.md) — Python and Kotlin style rules and project layout conventions.

## When to edit

Edit these files when you want a change to apply to **every future stage and every future run**. For per-run scope tweaks, edit [../setup/questionnaire.md](../setup/questionnaire.md) instead.
