async def test_login_no_otp(client):
    r = await client.post(
        "/api/auth/login", json={"msisdn": "+34600000001", "password": "secret123"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] >= 60


async def test_login_otp_challenge_then_verify(client):
    r = await client.post(
        "/api/auth/login", json={"msisdn": "+34600000002", "password": "secret123"}
    )
    assert r.status_code == 200
    assert r.json()["challenge"] == "OTP"
    challenge = r.json()["challengeToken"]
    r = await client.post(
        "/api/auth/otp/verify", json={"challengeToken": challenge, "code": "123456"}
    )
    assert r.status_code == 200
    assert "accessToken" in r.json()


async def test_invalid_credentials(client):
    r = await client.post(
        "/api/auth/login", json={"msisdn": "+34600000001", "password": "wrongpassword"}
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"
