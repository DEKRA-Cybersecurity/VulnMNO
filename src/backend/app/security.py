from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import get_settings

UTC = timezone.utc
_argon2 = PasswordHasher()

SEED_SALT = "vulnmno-seed-salt"


def hash_password(plain: str) -> str:
    return _argon2.hash(plain)


def verify_password(plain: str, stored_hash: str) -> bool:
    if stored_hash.startswith("seed$"):
        expected = "seed$" + hashlib.sha256((SEED_SALT + plain).encode()).hexdigest()
        return secrets.compare_digest(expected, stored_hash)
    try:
        return _argon2.verify(stored_hash, plain)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(stored_hash: str) -> bool:
    return stored_hash.startswith("seed$") or _argon2.check_needs_rehash(stored_hash)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def random_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def now() -> datetime:
    return datetime.now(UTC)


def to_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def make_access_token(customer_public_id: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    jti = secrets.token_hex(16)
    issued = now()
    expires = issued + timedelta(seconds=settings.access_token_ttl_seconds)
    payload: dict[str, Any] = {
        "sub": customer_public_id,
        "iat": int(issued.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": jti,
        "typ": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, jti, expires


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def make_refresh_token() -> tuple[str, str, datetime]:
    settings = get_settings()
    plain = random_token(32)
    return plain, sha256_hex(plain), now() + timedelta(seconds=settings.refresh_token_ttl_seconds)
