def test_normalize_webhook_url_adds_https_prefix_when_missing():
    # Es común pegar solo el dominio de Railway (sin esquema) — httpx no
    # acepta una URL así.
    from services.chat_service import _normalize_webhook_url

    assert _normalize_webhook_url("mi-n8n.up.railway.app/webhook/chat") == "https://mi-n8n.up.railway.app/webhook/chat"
    assert _normalize_webhook_url("https://ya-tiene-esquema.com/x") == "https://ya-tiene-esquema.com/x"
    assert _normalize_webhook_url("http://ya-tiene-esquema.com/x") == "http://ya-tiene-esquema.com/x"
    assert _normalize_webhook_url("") == ""
    assert _normalize_webhook_url("  ") == ""


class _FakeN8nResponse:
    def __init__(self, reply="Hola, ¿en qué te ayudo?"):
        self._reply = reply

    def raise_for_status(self):
        pass

    def json(self):
        return {"reply": self._reply}


def _register_and_login(client, email, full_name="Cliente JG", phone="3001234567"):
    client.post(
        "/auth/register",
        json={"email": email, "password": "supersecret123", "full_name": full_name, "phone": phone},
    )
    response = client.post("/auth/login", json={"email": email, "password": "supersecret123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_order(client, headers, product_id, guest_email, quantity=1):
    return client.post(
        "/orders",
        json={
            "guest_email": guest_email, "guest_name": "Cliente JG", "guest_phone": "3001234567",
            "shipping_address": "Calle 1 # 2-3", "shipping_city": "Bogotá",
            "items": [{"product_id": product_id, "quantity": quantity}],
        },
        headers=headers,
    )


def test_chat_message_anonymous_sends_empty_customer_context(client, monkeypatch):
    captured = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["headers"] = headers
        captured["json"] = json
        return _FakeN8nResponse()

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    response = client.post("/chat/message", json={"message": "Hola", "session_id": "abc123"})
    assert response.status_code == 200
    assert response.json()["reply"] == "Hola, ¿en qué te ayudo?"

    assert captured["json"]["is_logged_in"] is False
    assert captured["json"]["customer_context"] == ""
    assert captured["json"]["message"] == "Hola"
    assert captured["json"]["session_id"] == "abc123"
    assert captured["headers"]["X-Webhook-Secret"] == "test_n8n_secret"


def test_chat_message_authenticated_includes_own_recent_orders(client, admin_headers, monkeypatch):
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
    order = _create_order(client, admin_headers, product["id"], "admin@jgparfums.com").json()

    response = client.post(
        "/chat/message", json={"message": "¿cómo va mi pedido?", "session_id": "abc123"}, headers=admin_headers
    )
    assert response.status_code == 200

    assert captured["json"]["is_logged_in"] is True
    context = captured["json"]["customer_context"]
    assert order["order_number"] in context
    assert "pendiente de pago" in context  # estado por defecto de un pedido recién creado
    assert "1x Oud Royal (frasco)" in context
    assert "$350.000" in context


def test_chat_context_isolated_between_users(client, admin_headers, monkeypatch):
    captured = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return _FakeN8nResponse()

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    product = client.post(
        "/products",
        json={
            "slug": "vainilla-bourbon", "name": "Vainilla Bourbon", "description": "Dulce.",
            "size_ml": 50, "price": 120000, "stock": 10,
        },
        headers=admin_headers,
    ).json()

    headers_a = _register_and_login(client, "cliente.a@example.com")
    headers_b = _register_and_login(client, "cliente.b@example.com")

    order_a = _create_order(client, headers_a, product["id"], "cliente.a@example.com").json()
    order_b = _create_order(client, headers_b, product["id"], "cliente.b@example.com").json()

    response = client.post(
        "/chat/message", json={"message": "¿cómo va mi pedido?", "session_id": "abc123"}, headers=headers_a
    )
    assert response.status_code == 200
    context = captured["json"]["customer_context"]

    assert order_a["order_number"] in context
    assert order_b["order_number"] not in context
    assert "cliente.a@example.com" not in context
    assert "cliente.b@example.com" not in context


def test_chat_customer_context_excludes_address_phone_email_and_payment(client, admin_headers, monkeypatch):
    import json as json_module

    captured = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return _FakeN8nResponse()

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    product = client.post(
        "/products",
        json={
            "slug": "sandalo-mistico", "name": "Sándalo Místico", "description": "Amaderado.",
            "size_ml": 100, "price": 280000, "stock": 5,
        },
        headers=admin_headers,
    ).json()
    headers = _register_and_login(client, "cliente.privado@example.com", phone="3007654321")
    _create_order(client, headers, product["id"], "cliente.privado@example.com")

    client.post(
        "/chat/message", json={"message": "¿cómo va mi pedido?", "session_id": "abc123"}, headers=headers
    )

    payload_dump = json_module.dumps(captured["json"]).lower()
    # nada del payload completo (no solo customer_context) debe filtrar estos
    # campos: dirección, teléfono, correo, documento, datos de pago/pasarela.
    for forbidden in [
        "calle 1", "3007654321", "cliente.privado@example.com",
        "bogotá", "shipping_address", "shipping_city", "guest_phone",
        "guest_email", "payment_reference", "token",
    ]:
        assert forbidden not in payload_dump, f"campo sensible filtrado al payload: {forbidden!r}"


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
    # apiFetch en api.js) — solo se trata como visitante sin sesión, con
    # customer_context vacío y sin error.
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
    assert captured["json"]["is_logged_in"] is False
    assert captured["json"]["customer_context"] == ""


def test_chat_authenticated_user_without_orders_gets_neutral_context(client, monkeypatch):
    captured = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return _FakeN8nResponse()

    monkeypatch.setattr("services.chat_service.httpx.post", _fake_post)

    headers = _register_and_login(client, "sin.pedidos@example.com")
    response = client.post(
        "/chat/message", json={"message": "¿tengo pedidos?", "session_id": "abc123"}, headers=headers
    )
    assert response.status_code == 200
    assert captured["json"]["is_logged_in"] is True
    assert captured["json"]["customer_context"] != ""


def test_build_customer_context_truncates_to_max_chars(db):
    from datetime import datetime, timezone

    from middleware.auth import hash_password
    from models.order import Order
    from models.order_item import OrderItem
    from models.user import User
    from routes.chat import _MAX_CONTEXT_CHARS, build_customer_context

    user = User(email="muchos.pedidos@example.com", password_hash=hash_password("x12345678"), full_name="Cliente")
    db.add(user)
    db.commit()
    db.refresh(user)

    for i in range(5):
        order = Order(
            order_number=f"JG-TEST-{i}",
            user_id=user.id,
            guest_email=user.email,
            guest_name="Cliente",
            guest_phone="3000000000",
            shipping_address="Calle larga " * 5,
            shipping_city="Bogotá",
            subtotal=100000,
            shipping_cost=0,
            total=100000,
            items=[
                OrderItem(
                    product_name="Un Perfume Con Nombre Bastante Largo Para Forzar El Recorte",
                    size_ml=None,
                    unit_price=100000,
                    quantity=1,
                )
            ],
        )
        db.add(order)
    db.commit()

    context, is_logged_in = build_customer_context(db, user)
    assert is_logged_in is True
    assert len(context) <= _MAX_CONTEXT_CHARS + 1  # +1 por el "…" de corte
