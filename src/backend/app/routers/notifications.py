from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_customer, get_session
from app.models import Customer, DeviceToken, Notification
from app.schemas.common import Page
from app.schemas.notification import (
    DeviceTokenRegister,
    NotificationPreferences,
    NotificationPreferencesUpdate,
    NotificationRead,
)
from app.services.pagination import paginate

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _to_read(n: Notification, customer_public_id: str) -> NotificationRead:
    return NotificationRead(
        notificationId=n.public_id,
        customerId=customer_public_id,
        channel=n.channel,
        messageType=n.message_type,
        title=n.title,
        body=n.body,
        createdAt=n.created_at,
        readAt=n.read_at,
    )


@router.get("", response_model=Page[NotificationRead])
async def list_notifications(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
):
    rows, nxt = await paginate(
        session,
        select(Notification).where(Notification.customer_id == customer.id),
        id_column=Notification.id,
        limit=limit,
        cursor=cursor,
    )
    return Page(items=[_to_read(n, customer.public_id) for n in rows], nextCursor=nxt)


@router.post("/preferences", response_model=NotificationPreferences)
async def update_preferences(
    body: NotificationPreferencesUpdate,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    prefs = dict(customer.notification_preferences or {})
    for k, v in body.model_dump(exclude_none=True).items():
        prefs[k] = v
    # Ensure all four keys exist
    for k in ("push", "sms", "email", "inApp"):
        prefs.setdefault(k, True)
    customer.notification_preferences = prefs
    await session.flush()
    return NotificationPreferences(**prefs)


@router.post("/device-token", status_code=status.HTTP_204_NO_CONTENT)
async def register_device_token(
    body: DeviceTokenRegister,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    existing = (
        await session.execute(select(DeviceToken).where(DeviceToken.token == body.token))
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            DeviceToken(
                customer_id=customer.id,
                token=body.token,
                platform=body.platform,
                app_version=body.appVersion,
            )
        )
    else:
        existing.customer_id = customer.id
        existing.app_version = body.appVersion
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
