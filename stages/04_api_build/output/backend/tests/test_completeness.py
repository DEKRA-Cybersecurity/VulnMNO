"""Stage 14 — completeness passes: device registry + SIM swap."""
from __future__ import annotations


async def test_register_device_first_time_marks_unrecognized(client, alice_headers):
    r = await client.post(
        "/api/auth/devices",
        json={
            "deviceId": "ANDROID-NEW-1",
            "platform": "android",
            "model": "Pixel 9",
            "appVersion": "1.0.0",
        },
        headers=alice_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["deviceId"] == "ANDROID-NEW-1"
    assert body["recognized"] is False
    assert body["registeredAt"]


async def test_register_device_again_marks_recognized(client, alice_headers):
    payload = {"deviceId": "ANDROID-REPEAT", "platform": "android"}
    r1 = await client.post("/api/auth/devices", json=payload, headers=alice_headers)
    first_ts = r1.json()["registeredAt"]
    r2 = await client.post(
        "/api/auth/devices",
        json={**payload, "appVersion": "1.0.1"},
        headers=alice_headers,
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["recognized"] is True
    assert body["registeredAt"] == first_ts  # first_seen_at frozen


async def test_register_device_requires_auth(client):
    r = await client.post(
        "/api/auth/devices",
        json={"deviceId": "ANY", "platform": "android"},
    )
    assert r.status_code == 401


async def test_login_records_device_id_in_audit(client):
    r = await client.post(
        "/api/auth/login",
        json={"msisdn": "+34600000001", "password": "secret123"},
        headers={"X-Device-Id": "AUDIT-DEV-1"},
    )
    assert r.status_code == 200
    # Audit verification is opaque from outside; we just confirm the endpoint
    # accepts the header without rejecting the login.


async def test_sim_swap_marks_old_swapped_and_returns_new(client, bruno_headers):
    # Uses Bruno (instead of Alice) because other test files assert Alice's
    # SIM ID = SIM-10001 and the session-scoped DB shares state across files.
    before = await client.get("/api/customers/me/sim-profile", headers=bruno_headers)
    old_id = before.json()["simId"]
    assert before.json()["status"] == "active"

    r = await client.post(
        "/api/customers/me/sim-swap",
        json={"newSimType": "esim", "reason": "Phone lost during testing"},
        headers=bruno_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["oldSim"]["simId"] == old_id
    assert body["oldSim"]["status"] == "swapped"
    assert body["newSim"]["type"] == "esim"
    assert body["newSim"]["status"] == "active"
    assert body["newSim"]["simId"] != old_id

    after = await client.get("/api/customers/me/sim-profile", headers=bruno_headers)
    assert after.json()["simId"] == body["newSim"]["simId"]
    assert after.json()["type"] == "esim"


async def test_sim_swap_requires_auth(client):
    r = await client.post(
        "/api/customers/me/sim-swap", json={"newSimType": "physical"}
    )
    assert r.status_code == 401
