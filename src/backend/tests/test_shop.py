async def test_list_products(client, alice_headers):
    r = await client.get("/api/shop/products", headers=alice_headers)
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(p["productId"] == "DATA-10GB-7D" for p in items)


async def test_apply_promo_and_purchase(client, alice_headers):
    r = await client.post(
        "/api/shop/promotions/apply",
        headers=alice_headers,
        json={"productId": "DATA-10GB-7D", "promoCode": "SUMMER20"},
    )
    assert r.status_code == 200 and r.json()["finalPrice"] == "7.99"
    r = await client.post(
        "/api/shop/purchases",
        headers=alice_headers,
        json={"productId": "DATA-10GB-7D", "promoCode": "SUMMER20"},
    )
    assert r.status_code == 201 and r.json()["status"] == "confirmed"


async def test_invalid_promo(client, alice_headers):
    r = await client.post(
        "/api/shop/promotions/apply",
        headers=alice_headers,
        json={"productId": "DATA-10GB-7D", "promoCode": "DOES-NOT-EXIST"},
    )
    assert r.status_code == 400 and r.json()["error"]["code"] == "PROMO_INVALID"


async def test_purchase_404_for_other_customer(client, alice_headers):
    r = await client.get("/api/shop/purchases/PUR-99999", headers=alice_headers)
    assert r.status_code == 404
