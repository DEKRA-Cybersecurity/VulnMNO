async def test_create_then_message_then_close(client, alice_headers):
    r = await client.post(
        "/api/support/tickets",
        headers=alice_headers,
        json={"topic": "Technical", "description": "Cannot connect"},
    )
    assert r.status_code == 201
    tid = r.json()["ticketId"]

    r = await client.post(
        f"/api/support/tickets/{tid}/messages",
        headers=alice_headers,
        json={"body": "Update"},
    )
    assert r.status_code == 201

    r = await client.post(f"/api/support/tickets/{tid}/close", headers=alice_headers)
    assert r.status_code == 200 and r.json()["status"] == "closed"

    r = await client.post(
        f"/api/support/tickets/{tid}/messages",
        headers=alice_headers,
        json={"body": "after close"},
    )
    assert r.status_code == 409 and r.json()["error"]["code"] == "TICKET_CLOSED"


async def test_cross_customer_ticket_returns_404(client, alice_headers, bruno_headers):
    r = await client.post(
        "/api/support/tickets",
        headers=bruno_headers,
        json={"topic": "Other", "description": "Bruno's ticket"},
    )
    bruno_tid = r.json()["ticketId"]
    r = await client.get(f"/api/support/tickets/{bruno_tid}", headers=alice_headers)
    assert r.status_code == 404
