"""Audit-event → Notification + push delivery glue.

Customer-facing event types trigger a Notification row + a call to the configured push
adapter. Drives `Notification.delivery_status` per the contract:
- queued  → before send
- sent    → push.send() returned success
- failed  → returned failure (transient or permanent)
- skipped → customer's notification_preferences.push is false
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ids import next_notification_id
from app.models import Customer, DeviceToken, Notification

from . import get_push_delivery

log = logging.getLogger("vulnmno.push.audit_hook")

# Mapping: audit event_type → Notification (channel, message_type, i18n title key).
_DISPATCH = {
    "PURCHASE_COMPLETED": ("push", "purchase_confirmation", "Purchase confirmed"),
    "PLAN_CHANGE": ("push", "plan_change", "Plan updated"),
    "BALANCE_LOW": ("push", "low_balance", "Wallet running low"),
    "REFUND_APPROVED": ("push", "support_update", "Refund approved"),
}


async def maybe_send_push(
    session: AsyncSession,
    *,
    event_type: str,
    actor_id: str | None,
    target_id: str | None,
    payload: dict | None,
) -> None:
    spec = _DISPATCH.get(event_type)
    if spec is None or actor_id is None:
        return  # not a customer-facing event we push for

    channel, msg_type, default_title = spec
    customer = (
        await session.execute(select(Customer).where(Customer.public_id == actor_id))
    ).scalar_one_or_none()
    if customer is None or customer.deleted_at is not None:
        return

    prefs = customer.notification_preferences or {}
    title = default_title
    body = _body_from_payload(event_type, payload or {})

    notif = Notification(
        public_id=await next_notification_id(session),
        customer_id=customer.id,
        channel=channel,
        message_type=msg_type,
        title=title,
        body=body,
        delivery_status="queued",
    )
    session.add(notif)
    await session.flush()

    if not prefs.get("push", True):
        notif.delivery_status = "skipped"
        return

    token_row = (
        await session.execute(select(DeviceToken).where(DeviceToken.customer_id == customer.id))
    ).scalars().first()
    if token_row is None:
        # No device registered — record and move on (still not a failure of the audit op).
        notif.delivery_status = "failed"
        log.info("push skipped: customer %s has no device token", actor_id)
        return

    push = get_push_delivery()
    result = await push.send(
        customer_id=actor_id,
        notification_id=notif.public_id,
        title=title,
        body=body,
        data={"event_type": event_type, "target_id": target_id or "", "__token": token_row.token},
    )
    if result.success:
        notif.delivery_status = "sent"
        notif.delivered_at = datetime.now(timezone.utc)
        notif.provider_message_id = result.provider_message_id
    else:
        notif.delivery_status = "failed"
        log.warning("push failed: %s %s", result.error_code, result.error_message)


def _body_from_payload(event_type: str, payload: dict) -> str:
    if event_type == "PURCHASE_COMPLETED":
        price = payload.get("finalPrice")
        prod = payload.get("productId", "")
        return f"Your purchase of {prod} for {price} EUR is confirmed."
    if event_type == "PLAN_CHANGE":
        mode = payload.get("mode", "immediate")
        return f"Your plan change was {'applied' if mode == 'immediate' else 'scheduled'}."
    if event_type == "BALANCE_LOW":
        return "Your wallet balance is below €5. Top up to avoid service interruption."
    if event_type == "REFUND_APPROVED":
        return "Your refund has been approved and will be reflected in your wallet shortly."
    return "VulnMNO update"
