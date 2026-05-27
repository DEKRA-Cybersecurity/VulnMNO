async def test_get_me_matches_seed(client, alice_headers):
    r = await client.get("/api/customers/me", headers=alice_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["customerId"] == "CUST-10001"
    assert body["primaryMsisdn"] == "+34600000001"
    assert body["accountType"] == "prepaid"


async def test_get_me_requires_auth(client):
    r = await client.get("/api/customers/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_lines_and_sim(client, alice_headers):
    r = await client.get("/api/customers/me/lines", headers=alice_headers)
    assert r.status_code == 200 and len(r.json()["items"]) == 1
    r = await client.get("/api/customers/me/sim-profile", headers=alice_headers)
    assert r.status_code == 200 and r.json()["simId"] == "SIM-10001"
