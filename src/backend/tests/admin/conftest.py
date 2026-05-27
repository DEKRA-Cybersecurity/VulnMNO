"""Admin-specific test fixtures: helper to log in with a given role and return a CSRF-aware client."""

from __future__ import annotations

import re

import pytest_asyncio


async def _login(client, username: str, password: str = "admin1234") -> str:
    r = await client.get("/admin/login")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
    r = await client.post(
        "/admin/login",
        data={"username": username, "password": password, "csrf_token": csrf, "next": "/admin/"},
    )
    assert r.status_code == 303, r.text
    # Fetch a fresh CSRF token bound to the now-authenticated session.
    r = await client.get("/admin/")
    return re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)


@pytest_asyncio.fixture
async def ops_csrf(client):
    return await _login(client, "ops")


@pytest_asyncio.fixture
async def support_csrf(client):
    return await _login(client, "support")


@pytest_asyncio.fixture
async def billing_csrf(client):
    return await _login(client, "billing")


@pytest_asyncio.fixture
async def security_csrf(client):
    return await _login(client, "security")
