import pytest

from services.urls import frontend_base_url, frontend_origins

MULTI = "https://jgparfums.com.co, https://jg-parfums.pages.dev/"


def test_frontend_origins_split_strip_and_drop_trailing_slash(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", MULTI)

    assert frontend_origins() == ["https://jgparfums.com.co", "https://jg-parfums.pages.dev"]
    assert frontend_base_url() == "https://jgparfums.com.co"


@pytest.mark.parametrize("value", ["", " , "])
def test_frontend_origins_fall_back_to_default_when_empty(monkeypatch, value):
    monkeypatch.setenv("FRONTEND_URL", value)

    assert frontend_base_url() == "http://localhost:8000"


def test_reset_password_link_uses_only_the_first_origin(client, db, monkeypatch):
    from middleware.auth import hash_password
    from models.user import User

    monkeypatch.setenv("FRONTEND_URL", MULTI)
    db.add(User(email="cliente@example.com", password_hash=hash_password("supersecret123"), full_name="Cliente"))
    db.commit()
    sent = []
    monkeypatch.setattr("routes.auth.email_reset_password", lambda to, url: sent.append((to, url)))

    response = client.post("/auth/forgot-password", json={"email": "cliente@example.com"})

    assert response.status_code == 200
    assert len(sent) == 1
    url = sent[0][1]
    assert url.startswith("https://jgparfums.com.co/reset-password.html?token=")
    assert "," not in url and "pages.dev" not in url


def test_payment_redirect_urls_use_only_the_first_origin(client, admin_headers, monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", MULTI)
    product = client.post(
        "/products",
        json={"slug": "oud-royal", "name": "Oud Royal", "description": "x", "size_ml": 100, "price": 350000, "stock": 5},
        headers=admin_headers,
    ).json()
    order = client.post(
        "/orders",
        json={
            "guest_email": "comprador@example.com",
            "guest_name": "Comprador",
            "guest_phone": "3001234567",
            "shipping_address": "Calle 1",
            "shipping_city": "Bogotá",
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
    ).json()
    captured = {}

    def _fake_config(reference, amount, redirect_url):
        captured["redirect_url"] = redirect_url
        return {"reference": reference, "public_key": "pub", "signature_integrity": "sig"}

    monkeypatch.setattr("routes.payments.wompi_service.build_checkout_config", _fake_config)

    response = client.post(f"/payments/wompi/{order['order_number']}")

    assert response.status_code == 200
    assert captured["redirect_url"] == f"https://jgparfums.com.co/pedido-confirmado.html?order={order['order_number']}"
