from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Union

import httpx
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_customer, get_session
from app.models import Customer, CustomerDevice
from app.schemas.auth import (
    DeviceRegisterRequest,
    DeviceRegisterResult,
    LoginRequest,
    OtpChallenge,
    OtpVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenPair,
)
from app.services import auth as auth_service
from app.services.audit import write_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


from app.rate_limit import limiter


@router.post("/login", response_model=Union[TokenPair, OtpChallenge])
@limiter.limit("5/minute")
async def login(
    body: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await auth_service.login(session, body.msisdn, body.password)
    if isinstance(result, TokenPair):
        # Per docs §12.1, LOGIN_SUCCESS carries a deviceId. The client sends it
        # via X-Device-Id; absence is acceptable (device registration is optional
        # per §13.1).
        device_id = request.headers.get("X-Device-Id")
        await write_audit(
            session,
            event_type="LOGIN_SUCCESS",
            actor_id=None,
            target_type="customer",
            target_id=None,
            payload={"msisdn": body.msisdn, "deviceId": device_id},
            ip_address=request.client.host if request.client else None,
        )
    return result


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    await auth_service.logout(session, customer, access_jti=None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await auth_service.refresh(session, body.refreshToken)


@router.post("/otp/verify", response_model=TokenPair)
async def otp_verify(
    body: OtpVerifyRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await auth_service.verify_otp(session, body.challengeToken, body.code)


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset_request(
    body: PasswordResetRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    await auth_service.request_password_reset(session, body.msisdn)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset_confirm(
    body: PasswordResetConfirm,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    await auth_service.confirm_password_reset(session, body.msisdn, body.code, body.newPassword)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/devices", response_model=DeviceRegisterResult)
async def register_device(
    body: DeviceRegisterRequest,
    request: Request,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Logical device registration (docs §10.1). Distinct from the FCM push
    token endpoint at /api/notifications/device-token: that one stores a
    delivery target, this one stores a stable per-device identifier used for
    audit and trusted-device decisions."""
    now = datetime.now(timezone.utc)
    existing = (
        await session.execute(
            select(CustomerDevice).where(
                CustomerDevice.customer_id == customer.id,
                CustomerDevice.device_id == body.deviceId,
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        record = CustomerDevice(
            customer_id=customer.id,
            device_id=body.deviceId,
            platform=body.platform,
            model=body.model,
            app_version=body.appVersion,
            first_seen_at=now,
            last_seen_at=now,
            trusted=False,
        )
        session.add(record)
        recognized = False
        registered_at = now
    else:
        existing.last_seen_at = now
        if body.appVersion is not None:
            existing.app_version = body.appVersion
        if body.model is not None:
            existing.model = body.model
        recognized = True
        registered_at = existing.first_seen_at

    await session.flush()

    if body.callbackUrl:
        # API7 training lab (OWASP API Security Top 10) — see
        # src/docs/vulns/api/API7-Server-Side-Request-Forgery.md.
        # "Verifies" the callback URL is reachable with an unrestricted
        # server-side fetch: no scheme/host allowlist, no private/link-local
        # range block.
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.get(body.callbackUrl)
        except httpx.HTTPError:
            pass

    await write_audit(
        session,
        event_type="DEVICE_REGISTERED" if not recognized else "DEVICE_SEEN",
        actor_id=customer.public_id,
        target_type="device",
        target_id=body.deviceId,
        payload={"platform": body.platform, "model": body.model, "appVersion": body.appVersion},
        ip_address=request.client.host if request.client else None,
    )

    # SQLite drops tz info; force UTC on the way out so the API contract is stable
    # regardless of backend (Postgres preserves tz, SQLite doesn't).
    if registered_at.tzinfo is None:
        registered_at = registered_at.replace(tzinfo=timezone.utc)
    return DeviceRegisterResult(
        deviceId=body.deviceId,
        recognized=recognized,
        registeredAt=registered_at.isoformat(),
    )
