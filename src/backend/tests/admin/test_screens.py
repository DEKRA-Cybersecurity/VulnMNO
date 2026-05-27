async def test_dashboard(client, ops_csrf):
    r = await client.get("/admin/")
    assert r.status_code == 200
    assert "Customers" in r.text and "Pending refunds" in r.text


async def test_customer_search(client, ops_csrf):
    r = await client.get("/admin/customers?q=alice")
    assert r.status_code == 200
    assert "CUST-10001" in r.text


async def test_customer_detail(client, ops_csrf):
    r = await client.get("/admin/customers/CUST-10001")
    assert r.status_code == 200
    assert "Wallet balance" in r.text


async def test_customer_404_for_unknown_id(client, ops_csrf):
    r = await client.get("/admin/customers/CUST-99999")
    assert r.status_code == 404


async def test_plans_list_visible(client, ops_csrf):
    r = await client.get("/admin/plans")
    assert r.status_code == 200
    assert "PREPAID-PLUS" in r.text


async def test_promotions_list_visible(client, ops_csrf):
    r = await client.get("/admin/promotions")
    assert r.status_code == 200
    assert "PROMO-SUMMER-2026" in r.text


async def test_tickets_list_visible(client, ops_csrf):
    r = await client.get("/admin/tickets")
    assert r.status_code == 200
    assert "Support tickets" in r.text


async def test_refunds_list_visible(client, ops_csrf):
    r = await client.get("/admin/refunds")
    assert r.status_code == 200
    assert "Refunds" in r.text


async def test_audit_list_visible(client, ops_csrf):
    r = await client.get("/admin/audit")
    assert r.status_code == 200
    assert "Audit log" in r.text


async def test_reports_visible(client, ops_csrf):
    r = await client.get("/admin/reports")
    assert r.status_code == 200
    assert "Reports" in r.text


async def test_staff_list_visible_to_ops_admin(client, ops_csrf):
    r = await client.get("/admin/staff")
    assert r.status_code == 200
    assert "Admin staff" in r.text
