"""Admin session + CSRF primitives.

Sessions use Starlette's SessionMiddleware (signed cookies). We add:
- a CSRF token issued at login and rotated on every privilege change,
- helpers to bind the current AdminUser id to the session.
"""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import Request

from app.config import get_settings
from app.security import hash_password, verify_password  # reuse Argon2id

ADMIN_SESSION_KEY = "admin"
CSRF_SESSION_KEY = "csrf"


def set_admin_session(request: Request, *, admin_id: int, admin_public_id: str, role: str) -> str:
    """Establish admin session and return a fresh CSRF token."""
    settings = get_settings()
    csrf = secrets.token_urlsafe(settings.admin_csrf_token_bytes)
    request.session[ADMIN_SESSION_KEY] = {
        "id": admin_id,
        "public_id": admin_public_id,
        "role": role,
    }
    request.session[CSRF_SESSION_KEY] = csrf
    return csrf


def clear_admin_session(request: Request) -> None:
    request.session.pop(ADMIN_SESSION_KEY, None)
    request.session.pop(CSRF_SESSION_KEY, None)


def current_session_csrf(request: Request) -> str | None:
    return request.session.get(CSRF_SESSION_KEY)


def current_session_admin(request: Request) -> dict[str, Any] | None:
    return request.session.get(ADMIN_SESSION_KEY)


def verify_csrf(request: Request, submitted_token: str | None) -> bool:
    expected = current_session_csrf(request)
    if not expected or not submitted_token:
        return False
    return secrets.compare_digest(expected, submitted_token)


# Re-export password helpers under admin-namespace for clarity at call site.
def hash_admin_password(plain: str) -> str:
    return hash_password(plain)


def verify_admin_password(plain: str, stored_hash: str) -> bool:
    return verify_password(plain, stored_hash)
