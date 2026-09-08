def test_register_then_me(client):
    response = client.post(
        "/auth/register",
        json={"email": "cliente@example.com", "password": "supersecret123", "full_name": "Cliente Test"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "cliente@example.com"


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "supersecret123", "full_name": "Dup"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400


def test_login_wrong_password_generic_message(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "supersecret123", "full_name": "User"},
    )
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "wrongpass"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


def test_login_unknown_email_same_message_as_wrong_password(client):
    response = client.post("/auth/login", json={"email": "nadie@example.com", "password": "whatever123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


def test_me_without_token_rejected(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_forgot_password_generic_response_for_unknown_email(client):
    response = client.post("/auth/forgot-password", json={"email": "nadie@example.com"})
    assert response.status_code == 200
    assert "Si el email existe" in response.json()["message"]
