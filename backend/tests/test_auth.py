def test_identity(citizen):
    assert citizen.get("/api/auth/me").json()["role"] == "citizen"
    assert citizen.post("/api/auth/logout").is_success
    assert citizen.get("/api/auth/me").status_code == 401
    assert citizen.post(
        "/api/auth/login", json={"email": "student@example.org", "password": "A long passphrase"}
    ).is_success


def test_foreign_origin(client):
    assert client.post("/api/auth/logout", headers={"Origin": "https://other.example"}).status_code == 403
