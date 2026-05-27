"""Jinja2 environment factory for admin templates.

Templates live at `<backend>/templates/admin/`. Custom filters cover the formatting
patterns the admin views use heavily (money, datetimes, CSRF hidden input).
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from .security import current_session_admin, current_session_csrf

# Search root is `<backend>/templates/`. Template names always include the `admin/` prefix
# (e.g. `admin/login.html`) so the {% extends "admin/base.html" %} references resolve.
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def _format_money(value: Decimal | float | int | None, currency: str = "EUR") -> str:
    if value is None:
        return "—"
    d = Decimal(value) if not isinstance(value, Decimal) else value
    return f"{d:,.2f} {currency}"


def _format_datetime(value: datetime | str | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")


def _csrf_input(csrf_token: str | None) -> Markup:
    token = csrf_token or ""
    return Markup(f'<input type="hidden" name="csrf_token" value="{token}">')


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters["money"] = _format_money
templates.env.filters["dt"] = _format_datetime
templates.env.globals["csrf_input"] = _csrf_input


def render(
    request: Request,
    name: str,
    context: dict | None = None,
    *,
    status_code: int = 200,
):
    """Render a template with the admin's session info auto-injected.

    Pass `name` as `admin/<file>` (e.g. `admin/dashboard.html`). HTMX-aware callers
    typically pass fragment names like `admin/_partials/customers_table.html`.
    """
    ctx = dict(context or {})
    ctx.setdefault("admin_session", current_session_admin(request))
    ctx.setdefault("csrf_token", current_session_csrf(request))
    ctx.setdefault("is_htmx", request.headers.get("HX-Request") == "true")
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
