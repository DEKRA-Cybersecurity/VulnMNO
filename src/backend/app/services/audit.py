from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent

log = logging.getLogger("vulnmno.audit")


async def write_audit(
    session: AsyncSession,
    *,
    event_type: str,
    actor_id: str | None,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    try:
        session.add(
            AuditEvent(
                event_type=event_type,
                actor_id=actor_id,
                target_type=target_type,
                target_id=target_id,
                payload=payload or {},
                ip_address=ip_address,
            )
        )
        await session.flush()
    except Exception as exc:
        log.warning("audit write failed: %s", exc)
        return

    # Phase 2 — fan out to push delivery for customer-facing events. Errors here are
    # logged but never break the audit write (best-effort by design).
    try:
        from app.push.audit_hook import maybe_send_push

        await maybe_send_push(
            session,
            event_type=event_type,
            actor_id=actor_id,
            target_id=target_id,
            payload=payload,
        )
    except Exception as exc:
        log.warning("push fan-out failed: %s", exc)
