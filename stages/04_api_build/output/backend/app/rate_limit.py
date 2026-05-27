"""Rate limiting via slowapi. See `app/main.py` for wiring.

Customers are keyed by their `Authorization` bearer token's `sub` claim when available;
otherwise we fall back to the client IP. Admin endpoints use IP directly.
"""

from __future__ import annotations

import os

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings


def _customer_or_ip(request: Request) -> str:
    """Use JWT sub as the rate-limit key if a Bearer token is present; otherwise IP."""
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:]
        try:
            import jwt
            payload = jwt.decode(
                token,
                get_settings().jwt_secret,
                algorithms=["HS256"],
                options={"verify_signature": True, "verify_exp": False},
            )
            sub = payload.get("sub")
            if sub:
                return f"cust:{sub}"
        except Exception:
            pass
    return f"ip:{get_remote_address(request)}"


# Read the env directly at module import time. Tests set
# `VULNMNO_RATE_LIMIT_ENABLED=false` in conftest before importing app.main; the
# `@limiter.limit(...)` decorators bind to this `enabled` flag, so flipping it after
# decoration would not propagate. The env-direct read sidesteps that.
_enabled = os.environ.get("VULNMNO_RATE_LIMIT_ENABLED", "true").strip().lower() != "false"
limiter = Limiter(key_func=_customer_or_ip, enabled=_enabled)


def is_enabled() -> bool:
    return get_settings().rate_limit_enabled
