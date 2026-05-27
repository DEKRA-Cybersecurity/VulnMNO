async def test_current_and_available(client, alice_headers):
    r = await client.get("/api/plans/current", headers=alice_headers)
    assert r.status_code == 200
    r = await client.get("/api/plans/available", headers=alice_headers)
    assert r.status_code == 200 and len(r.json()["items"]) >= 1


async def test_change_plan_immediate(client, alice_headers):
    r = await client.post(
        "/api/plans/change",
        headers=alice_headers,
        json={"planId": "PREPAID-BASIC", "mode": "immediate"},
    )
    assert r.status_code == 200 and r.json()["status"] == "applied"


async def test_plan_ineligible(client, alice_headers):
    # Alice is prepaid; UNLIMITED-PREMIUM is postpaid
    r = await client.post(
        "/api/plans/change",
        headers=alice_headers,
        json={"planId": "UNLIMITED-PREMIUM", "mode": "immediate"},
    )
    assert r.status_code == 400 and r.json()["error"]["code"] == "PLAN_INELIGIBLE"
