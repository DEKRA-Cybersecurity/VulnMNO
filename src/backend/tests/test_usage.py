async def test_usage_calls(client, alice_headers):
    r = await client.get("/api/usage/calls", headers=alice_headers)
    assert r.status_code == 200


async def test_usage_export_csv(client, alice_headers):
    r = await client.get("/api/usage/export?format=csv", headers=alice_headers)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")


async def test_usage_export_invalid_range(client, alice_headers):
    r = await client.get(
        "/api/usage/calls?from=2026-06-01T00:00:00Z&to=2026-05-01T00:00:00Z",
        headers=alice_headers,
    )
    assert r.status_code == 400 and r.json()["error"]["code"] == "VALIDATION_FAILED"
