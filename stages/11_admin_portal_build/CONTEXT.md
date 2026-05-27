# Stage 11 — Admin portal build

Implement the server-rendered admin portal inside the existing FastAPI backend. The mobile JWT API surface is **not** touched; the admin lives under `/admin/*` with cookie-session auth, CSRF on every mutation, HTMX for partial swaps, Bootstrap 5 (CDN) for styling, and a per-role permission matrix.

## Inputs

**Layer 4 (working):**
- `../09_phase2_contract/output/admin-endpoints.md`
- `../09_phase2_contract/output/openapi.yaml`
- `../09_phase2_contract/output/error-codes-delta.md`
- `../10_phase2_data_model/output/entities-delta.md`
- `../08_phase2_requirements/output/admin-rbac-matrix.md`

**Layer 3 (reference):**
- `../../_config/code-style.md` (Python project layout)
- `../../_config/tech-stack.md`

## Process

1. Add Jinja2 + itsdangerous to the backend `pyproject.toml` dependencies.
2. Implement `app/admin/` subpackage:
   - `security.py` — session middleware bootstrap, CSRF token issue/verify, signed cookie helpers, `verify_admin_password` wrapper.
   - `permissions.py` — single source of truth `PERMISSIONS: dict[Role, dict[Module, Access]]` mirroring the RBAC matrix.
   - `deps.py` — `get_current_admin`, `require_module`, `require_csrf` FastAPI dependencies.
   - `templates_loader.py` — Jinja2 `Environment` factory with template path resolution + custom filters (`format_money`, `format_datetime`, `csrf_input`).
   - `services/audit.py` — thin wrapper around `app.services.audit.write_audit` that always sets `actor_id=admin.public_id`.
   - `routers/{auth,dashboard,customers,plans,promotions,tickets,refunds,audit,reports,admin_users}.py`.
3. Implement templates under `templates/admin/`:
   - `base.html` — top navbar + sidebar + content + flash messages.
   - Module pages (full page renders) extend `base.html`.
   - HTMX fragments live under `templates/admin/_partials/` and do NOT extend `base.html`.
4. Implement minimal `static/admin/admin.css` (~50 lines) and `static/admin/admin.js` (~30 lines HTMX helpers).
5. Wire everything in `app/main.py`:
   - `app.mount("/static", StaticFiles(directory=...))`.
   - `app.add_middleware(SessionMiddleware, secret_key=settings.admin_session_secret, ...)`.
   - `app.include_router(admin_router)`.
   - Exception handler for `AppError` extended to detect `/admin/` requests and render HTML instead of JSON.
6. Add Phase-2 settings to `app/config.py`: `admin_session_secret`, `admin_session_max_age_seconds=8*3600`, `admin_csrf_token_bytes=32`.
7. Tests under `tests/admin/`: one happy-path per router + one RBAC-denial test (e.g. support_agent trying to approve a refund → 403).

## Outputs

Code committed in-place under `04_api_build/output/backend/`:
- `app/admin/` (Python subpackage, ~10 files).
- `templates/admin/` (Jinja2 templates).
- `static/admin/` (admin.css, admin.js).
- `tests/admin/` (pytest cases).

Stage-level outputs (`output/`):
- `admin-screens-built.md` — ADM-ID ↔ template + router map (mirror of stage 5/6 screens-built.md pattern).
- `coverage-summary.md` — pytest result + per-router coverage.
