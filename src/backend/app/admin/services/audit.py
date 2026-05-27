"""Admin-scoped wrapper for `app.services.audit.write_audit` — always carries the
admin's public_id as `actor_id`. Keeps event_type prefixed `ADMIN_*` per convention.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdminUser
from app.services.audit import write_audit


async def write_admin_audit(
    session: AsyncSession,
    *,
    admin: AdminUser,
    event_type: str,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    if not event_type.startswith("ADMIN_"):
        event_type = f"ADMIN_{event_type}"
    ip = request.client.host if (request is not None and request.client) else None
    await write_audit(
        session,
        event_type=event_type,
        actor_id=admin.public_id,
        target_type=target_type,
        target_id=target_id,
        payload=payload or {},
        ip_address=ip,
    )
