from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def app_instance():
    tmp = tempfile.mkdtemp(prefix="vulnmno-")
    db_path = Path(tmp) / "test.db"
    os.environ["VULNMNO_DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["VULNMNO_UPLOADS_DIR"] = str(Path(tmp) / "uploads")
    os.environ["VULNMNO_JWT_SECRET"] = "test-secret-please-change-in-prod"
    # Phase 2 — disable rate limiting in tests; pytest's repeated logins would trip it.
    os.environ["VULNMNO_RATE_LIMIT_ENABLED"] = "false"
    os.environ["VULNMNO_ADMIN_SESSION_SECRET"] = "test-admin-session-secret"

    # Reset the cached settings so env vars take effect.
    from app.config import get_settings

    get_settings.cache_clear()

    from app.main import app  # imported after env is set

    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture
async def client(app_instance) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://t") as cli:
        yield cli


@pytest_asyncio.fixture
async def alice_headers(client) -> dict[str, str]:
    r = await client.post(
        "/api/auth/login", json={"msisdn": "+34600000001", "password": "secret123"}
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}


@pytest_asyncio.fixture
async def bruno_headers(client) -> dict[str, str]:
    r = await client.post(
        "/api/auth/login", json={"msisdn": "+34600000002", "password": "secret123"}
    )
    challenge = r.json()["challengeToken"]
    r = await client.post(
        "/api/auth/otp/verify", json={"challengeToken": challenge, "code": "123456"}
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}
