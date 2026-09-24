class _FakeN8nResponse:
    def __init__(self, reply="Hola, ¿en qué te ayudo?"):
        self._reply = reply

    def raise_for_status(self):
        pass

    def json(self):
        return {"reply": self._reply}


def test_chat_message_anonymous_sends_unauthenticated_context(client, monkeypatch):
    captured = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["headers"] = headers
        captured["json"] = json
        return _FakeN8nResponse()

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    response = client.post("/chat/message", json={"message": "Hola", "session_id": "abc123"})
    assert response.status_code == 200
    assert response.json()["reply"] == "Hola, ¿en qué te ayudo?"

    assert captured["json"]["context"] == {"authenticated": False}
    assert captured["json"]["message"] == "Hola"
    assert captured["json"]["session_id"] == "abc123"
    assert captured["headers"]["X-Webhook-Secret"] == "test_n8n_secret"


def test_chat_message_authenticated_includes_recent_orders(client, admin_headers, monkeypatch):
    captured = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return _FakeN8nResponse()

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    product = client.post(
        "/products",
        json={
            "slug": "oud-royal", "name": "Oud Royal", "description": "Amaderado.",
            "size_ml": 100, "price": 350000, "stock": 5,
        },
        headers=admin_headers,
    ).json()
    client.post(
        "/orders",
        json={
            "guest_email": "admin@jgparfums.com", "guest_name": "Admin JG", "guest_phone": "3000000000",
            "shipping_address": "Calle 1", "shipping_city": "Bogotá",
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
        headers=admin_headers,
    )

    response = client.post(
        "/chat/message", json={"message": "¿cómo va mi pedido?", "session_id": "abc123"}, headers=admin_headers
    )
    assert response.status_code == 200

    context = captured["json"]["context"]
    assert context["authenticated"] is True
    assert context["user_email"] == "admin@jgparfums.com"
    assert len(context["recent_orders"]) == 1
    assert context["recent_orders"][0]["items"] == ["1x Oud Royal"]


def test_chat_message_returns_503_when_webhook_not_configured(client, monkeypatch):
    monkeypatch.setattr("services.chat_service.N8N_WEBHOOK_URL", "")

    response = client.post("/chat/message", json={"message": "Hola", "session_id": "abc123"})
    assert response.status_code == 503


def test_chat_message_returns_503_when_n8n_unreachable(client, monkeypatch):
    import httpx

    def _fake_post(*args, **kwargs):
        raise httpx.ConnectError("no se pudo conectar")

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    response = client.post("/chat/message", json={"message": "Hola", "session_id": "abc123"})
    assert response.status_code == 503


def test_chat_message_rejects_empty_message(client):
    response = client.post("/chat/message", json={"message": "", "session_id": "abc123"})
    assert response.status_code == 422


def test_chat_message_with_expired_or_invalid_token_treated_as_anonymous(client, monkeypatch):
    # get_optional_user es "optional" de verdad: un token vencido no debe
    # tumbar la ruta con 401 (el front redirige a login apenas ve eso, ver
    # apiFetch en api.js) — solo se trata como visitante sin sesión.
    captured = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return _FakeN8nResponse()

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    response = client.post(
        "/chat/message",
        json={"message": "Hola", "session_id": "abc123"},
        headers={"Authorization": "Bearer no-es-un-jwt-valido"},
    )
    assert response.status_code == 200
    assert captured["json"]["context"] == {"authenticated": False}
