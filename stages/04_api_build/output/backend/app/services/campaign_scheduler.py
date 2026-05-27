"""Periodic background task: open / close promotions based on `starts_at` / `ends_at`.

Wired in `app/main.py` lifespan as an `asyncio.create_task`. Sleeps `interval_seconds`
between sweeps. Idempotent: re-running over the same time window is a no-op.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import session_scope
from app.models import Promotion
from app.services.audit import write_audit

log = logging.getLogger("vulnmno.campaigns")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def _sweep(session: AsyncSession) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    promos = (await session.execute(select(Promotion))).scalars().all()
    opened = 0
    closed = 0
    for p in promos:
        rules = dict(p.eligibility_rules or {})
        status = rules.get("status", "active")
        if status == "draft" and _aware(p.starts_at) <= now < _aware(p.ends_at):
            rules["status"] = "active"
            p.eligibility_rules = rules
            opened += 1
            await write_audit(
                session, event_type="CAMPAIGN_OPENED", actor_id="SYSTEM",
                target_type="promotion", target_id=p.public_id,
            )
        elif status != "expired" and _aware(p.ends_at) < now:
            rules["status"] = "expired"
            p.eligibility_rules = rules
            closed += 1
            await write_audit(
                session, event_type="CAMPAIGN_CLOSED", actor_id="SYSTEM",
                target_type="promotion", target_id=p.public_id,
            )
    if opened or closed:
        log.info("campaign sweep: opened=%d closed=%d", opened, closed)
    return opened, closed


async def run_forever(stop: asyncio.Event | None = None) -> None:
    s = get_settings()
    while True:
        try:
            async with session_scope() as session:
                await _sweep(session)
        except Exception as exc:
            log.warning("campaign sweep failed: %s", exc)
        if stop is not None and stop.is_set():
            return
        try:
            await asyncio.wait_for(
                stop.wait() if stop else asyncio.sleep(s.campaign_scheduler_interval_seconds),
                timeout=s.campaign_scheduler_interval_seconds,
            )
        except asyncio.TimeoutError:
            continue
        else:
            if stop and stop.is_set():
                return
