import re


async def test_anon_redirects_to_login(client):
    r = await client.get("/admin/", follow_redirects=False)
    assert r.status_code == 303
    assert "/admin/login" in r.headers["location"]


async def test_login_form_renders_with_csrf(client):
    r = await client.get("/admin/login")
    assert r.status_code == 200
    assert "<form" in r.text
    assert re.search(r'name="csrf_token" value="[^"]+"', r.text)


async def test_wrong_password_returns_401(client):
    r = await client.get("/admin/login")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)
    r = await client.post(
        "/admin/login",
        data={"username": "ops", "password": "wrong", "csrf_token": csrf, "next": "/admin/"},
    )
    assert r.status_code == 401
    assert "Invalid credentials" in r.text


async def test_good_login_lands_on_dashboard(client, ops_csrf):
    r = await client.get("/admin/")
    assert r.status_code == 200
    assert "Dashboard" in r.text
    assert "ops_admin" in r.text  # the navbar shows the role


async def test_support_agent_cannot_adjust_balance(client, support_csrf):
    r = await client.post(
        "/admin/customers/CUST-10001/balance-adjust",
        data={"amount": "1.00", "reason": "should not be allowed", "csrf_token": support_csrf},
    )
    assert r.status_code == 403
    assert "ADMIN_FORBIDDEN" in r.text


async def test_billing_operator_can_adjust_balance(client, billing_csrf):
    r = await client.post(
        "/admin/customers/CUST-10001/balance-adjust",
        data={"amount": "2.50", "reason": "Refund correction smoke test", "csrf_token": billing_csrf},
    )
    assert r.status_code == 200
    assert "Balance updated" in r.text


async def test_security_analyst_can_view_audit(client, security_csrf):
    r = await client.get("/admin/audit")
    assert r.status_code == 200
    # The seeded admin user list itself doesn't trigger audit, but the prior
    # billing_operator balance adjust should have written one. Either way, the
    # page renders.
    assert "Audit log" in r.text


async def test_security_analyst_cannot_manage_staff(client, security_csrf):
    r = await client.get("/admin/staff")
    assert r.status_code == 403
    assert "ADMIN_FORBIDDEN" in r.text
