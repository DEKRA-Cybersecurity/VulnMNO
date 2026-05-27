from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.errors import AppError, ErrorCode, unauthenticated
from app.models import Customer
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_customer(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Customer:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise unauthenticated()
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise AppError(ErrorCode.TOKEN_EXPIRED, "Access token expired", http_status=401)
    except jwt.PyJWTError:
        raise unauthenticated()

    sub = payload.get("sub")
    typ = payload.get("typ")
    if typ != "access" or not isinstance(sub, str):
        raise unauthenticated()

    customer = (
        await session.execute(select(Customer).where(Customer.public_id == sub))
    ).scalar_one_or_none()
    if customer is None or customer.deleted_at is not None or customer.status != "active":
        raise unauthenticated("Customer not active")
    return customer


IdempotencyKey = Annotated[str | None, Header(alias="Idempotency-Key")]
