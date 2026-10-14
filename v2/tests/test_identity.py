def test_registration_login_and_private_profile(client):
    account = {
        "name": "Learner",
        "email": "learner@example.com",
        "password": "Strong-Demo-Password1",
    }
    created = client.post("/api/v1/auth/register", json=account)
    assert created.status_code == 201
    assert "password_hash" not in created.text
    assert created.json()["balance_minutes"] == 120
    assert client.post("/api/v1/auth/register", json=account).status_code == 409
    login = client.post(
        "/api/v1/auth/token", data={"username": account["email"], "password": account["password"]}
    )
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert client.get("/api/v1/me", headers=headers).json()["email"] == account["email"]
    assert client.get("/api/v1/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/token", data={"username": account["email"], "password": "incorrect"}
        ).status_code
        == 401
    )


def test_invalid_input_and_privilege_injection(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "X", "email": "bad", "password": "short", "is_admin": True},
    )
    assert response.status_code == 422
    assert "short" not in response.text


def test_health(client):
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").json() == {"status": "ready"}
