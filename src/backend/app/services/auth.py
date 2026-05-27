from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.errors import AppError, ErrorCode
from app.models import Customer, OtpChallenge, PasswordReset, RefreshToken
from app.schemas.auth import OtpChallenge as OtpChallengeSchema
from app.schemas.auth import TokenPair
from app.security import (
    hash_password,
    make_access_token,
    make_refresh_token,
    needs_rehash,
    now,
    random_token,
    sha256_hex,
    to_aware,
    verify_password,
)

log = logging.getLogger("vulnmno.auth")


async def issue_token_pair(session: AsyncSession, customer: Customer) -> TokenPair:
    settings = get_settings()
    access, jti, _expires = make_access_token(customer.public_id)
    refresh_plain, refresh_hash, refresh_expires = make_refresh_token()
    session.add(
        RefreshToken(
            customer_id=customer.id,
            token_hash=refresh_hash,
            access_jti=jti,
            expires_at=refresh_expires,
        )
    )
    customer.last_login_at = now()
    await session.flush()
    return TokenPair(
        accessToken=access,
        refreshToken=refresh_plain,
        expiresIn=settings.access_token_ttl_seconds,
    )


async def login(session: AsyncSession, msisdn: str, password: str) -> TokenPair | OtpChallengeSchema:
    customer = (
        await session.execute(select(Customer).where(Customer.primary_msisdn == msisdn))
    ).scalar_one_or_none()
    if customer is None or customer.deleted_at is not None:
        raise AppError(ErrorCode.INVALID_CREDENTIALS, "Wrong credentials", http_status=401)
    if not verify_password(password, customer.password_hash):
        raise AppError(ErrorCode.INVALID_CREDENTIALS, "Wrong credentials", http_status=401)
    if customer.status != "active":
        raise AppError(ErrorCode.INVALID_CREDENTIALS, "Wrong credentials", http_status=401)

    if needs_rehash(customer.password_hash):
        customer.password_hash = hash_password(password)

    if customer.otp_enrolled:
        settings = get_settings()
        token = random_token(32)
        code = customer.otp_fixed_code or f"{secrets.randbelow(10**6):06d}"
        session.add(
            OtpChallenge(
                customer_id=customer.id,
                challenge_token=token,
                code_hash=sha256_hex(code),
                expires_at=now() + timedelta(seconds=settings.otp_ttl_seconds),
            )
        )
        await session.flush()
        log.info("OTP issued msisdn=%s code=%s", msisdn, code)
        return OtpChallengeSchema(challengeToken=token, expiresIn=settings.otp_ttl_seconds)

    return await issue_token_pair(session, customer)


async def verify_otp(session: AsyncSession, challenge_token: str, code: str) -> TokenPair:
    settings = get_settings()
    challenge = (
        await session.execute(
            select(OtpChallenge).where(OtpChallenge.challenge_token == challenge_token)
        )
    ).scalar_one_or_none()
    if challenge is None or challenge.consumed_at is not None or to_aware(challenge.expires_at) < now():
        raise AppError(ErrorCode.OTP_INVALID, "OTP invalid", http_status=401)

    # NOTE (training lab — M3 Insecure Authentication): the attempts cap that
    # previously consumed the challenge once `challenge.attempts >=
    # settings.otp_max_attempts` was hit has been removed deliberately so the
    # 6-digit code is brute-forceable within the OTP TTL. The counter is still
    # incremented on every miss so blue-team exercises can detect the attack
    # by alerting on `OtpChallenge.attempts` growth, but the server no longer
    # uses it to short-circuit. Endpoint also remains un-rate-limited (see
    # routers/auth.py). Success ⇒ 200 + TokenPair, miss ⇒ 401 — the status
    # delta is the fuzz oracle.
    if sha256_hex(code) != challenge.code_hash:
        challenge.attempts += 1
        raise AppError(ErrorCode.OTP_INVALID, "OTP invalid", http_status=401)

    challenge.consumed_at = now()
    customer = (
        await session.execute(select(Customer).where(Customer.id == challenge.customer_id))
    ).scalar_one()
    return await issue_token_pair(session, customer)


async def refresh(session: AsyncSession, refresh_token: str) -> TokenPair:
    token_hash = sha256_hex(refresh_token)
    row = (
        await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    ).scalar_one_or_none()
    if row is None or to_aware(row.expires_at) < now():
        raise AppError(ErrorCode.TOKEN_EXPIRED, "Refresh token expired", http_status=401)
    if row.revoked_at is not None:
        # Reuse → revoke entire chain for this customer
        await _revoke_chain(session, row.customer_id, reason="chain_reuse")
        raise AppError(ErrorCode.TOKEN_REVOKED, "Refresh token revoked", http_status=401)

    customer = (
        await session.execute(select(Customer).where(Customer.id == row.customer_id))
    ).scalar_one_or_none()
    if customer is None or customer.status != "active":
        raise AppError(ErrorCode.TOKEN_REVOKED, "Refresh token revoked", http_status=401)

    row.revoked_at = now()
    row.revoked_reason = "rotated"
    return await issue_token_pair(session, customer)


async def logout(session: AsyncSession, customer: Customer, access_jti: str | None = None) -> None:
    if access_jti is None:
        # Without the access JTI we revoke all current refresh tokens for the customer
        for row in (
            (await session.execute(
                select(RefreshToken).where(
                    RefreshToken.customer_id == customer.id, RefreshToken.revoked_at.is_(None)
                )
            )).scalars().all()
        ):
            row.revoked_at = now()
            row.revoked_reason = "logout"
        return
    row = (
        await session.execute(
            select(RefreshToken).where(
                RefreshToken.customer_id == customer.id, RefreshToken.access_jti == access_jti
            )
        )
    ).scalar_one_or_none()
    if row is not None and row.revoked_at is None:
        row.revoked_at = now()
        row.revoked_reason = "logout"


async def _revoke_chain(session: AsyncSession, customer_id: int, *, reason: str) -> None:
    for row in (
        (
            await session.execute(
                select(RefreshToken).where(
                    RefreshToken.customer_id == customer_id, RefreshToken.revoked_at.is_(None)
                )
            )
        )
        .scalars()
        .all()
    ):
        row.revoked_at = now()
        row.revoked_reason = reason


async def request_password_reset(session: AsyncSession, msisdn: str) -> None:
    settings = get_settings()
    customer = (
        await session.execute(select(Customer).where(Customer.primary_msisdn == msisdn))
    ).scalar_one_or_none()
    if customer is None:
        return  # never leak existence
    code = f"{secrets.randbelow(10**6):06d}"
    session.add(
        PasswordReset(
            customer_id=customer.id,
            code_hash=sha256_hex(code),
            expires_at=now() + timedelta(seconds=settings.password_reset_ttl_seconds),
        )
    )
    log.info("PWRESET issued msisdn=%s code=%s", msisdn, code)


async def confirm_password_reset(
    session: AsyncSession, msisdn: str, code: str, new_password: str
) -> None:
    customer = (
        await session.execute(select(Customer).where(Customer.primary_msisdn == msisdn))
    ).scalar_one_or_none()
    if customer is None:
        raise AppError(ErrorCode.OTP_INVALID, "Reset failed", http_status=401)
    row = (
        await session.execute(
            select(PasswordReset)
            .where(PasswordReset.customer_id == customer.id, PasswordReset.consumed_at.is_(None))
            .order_by(PasswordReset.id.desc())
        )
    ).scalars().first()
    if row is None or to_aware(row.expires_at) < now() or sha256_hex(code) != row.code_hash:
        raise AppError(ErrorCode.OTP_INVALID, "Reset failed", http_status=401)
    row.consumed_at = now()
    customer.password_hash = hash_password(new_password)
    await _revoke_chain(session, customer.id, reason="password_reset")
