async def test_balance(client, alice_headers):
    r = await client.get("/api/accounts/me/balance", headers=alice_headers)
    assert r.status_code == 200
    assert r.json()["currency"] == "EUR"


async def test_topup_creates_transaction(client, alice_headers):
    r = await client.post(
        "/api/accounts/me/topup",
        headers=alice_headers,
        json={"amount": 5, "currency": "EUR"},
    )
    assert r.status_code == 201
    assert r.json()["type"] == "topup"


async def test_invoice_detail_and_pdf(client, bruno_headers):
    r = await client.get("/api/accounts/me/invoices/INV-20001", headers=bruno_headers)
    assert r.status_code == 200 and len(r.json()["lineItems"]) == 1
    r = await client.get(
        "/api/accounts/me/invoices/INV-20001/download", headers=bruno_headers
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
