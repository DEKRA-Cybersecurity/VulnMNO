async def test_list_notifications(client, alice_headers):
    r = await client.get("/api/notifications", headers=alice_headers)
    assert r.status_code == 200 and "items" in r.json()


async def test_update_preferences(client, alice_headers):
    r = await client.post(
        "/api/notifications/preferences",
        headers=alice_headers,
        json={"push": False, "sms": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["push"] is False and body["sms"] is False
    assert body["email"] is True and body["inApp"] is True


async def test_device_token_registration_204(client, alice_headers):
    r = await client.post(
        "/api/notifications/device-token",
        headers=alice_headers,
        json={"token": "device-abc-1234567890", "platform": "android"},
    )
    assert r.status_code == 204
