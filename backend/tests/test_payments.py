import hashlib
import hmac

from services import mercadopago_service, wompi_service


def _create_product(client, admin_headers, stock=5, price=350000):
    payload = {
        "slug": "oud-royal",
        "name": "Oud Royal",
        "description": "Amaderado oriental, para la noche.",
        "size_ml": 100,
        "price": price,
        "stock": stock,
    }
    return client.post("/products", json=payload, headers=admin_headers).json()


def _create_order(client, product_id):
    payload = {
        "guest_email": "comprador@example.com",
        "guest_name": "Comprador Test",
        "guest_phone": "3001234567",
        "shipping_address": "Calle 1 # 2-3",
        "shipping_city": "Bogotá",
        "items": [{"product_id": product_id, "quantity": 1}],
    }
    return client.post("/orders", json=payload).json()


def test_init_wompi_payment_returns_public_key_and_reference(client, admin_headers):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])

    response = client.post(f"/payments/wompi/{order['order_number']}")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "wompi"
    assert body["reference"] == order["order_number"]
    assert body["public_key"] == "pub_test_1234"
    assert body["integrity_signature"] == wompi_service.build_integrity_signature(
        order["order_number"], order["total"] * 100
    )


def test_wompi_webhook_updates_order_to_paid(client, admin_headers):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])
    client.post(f"/payments/wompi/{order['order_number']}")

    transaction = {
        "id": "txn-123",
        "status": "APPROVED",
        "reference": order["order_number"],
        "amount_in_cents": order["total"] * 100,
    }
    properties = ["transaction.id", "transaction.status", "transaction.amount_in_cents"]
    concatenated = "".join(str(transaction[prop.split(".")[1]]) for prop in properties)
    concatenated += "1700000000test_events_secret"
    checksum = hashlib.sha256(concatenated.encode("utf-8")).hexdigest()

    payload = {
        "event": "transaction.updated",
        "data": {"transaction": transaction},
        "signature": {"properties": properties, "checksum": checksum},
        "timestamp": 1700000000,
    }
    response = client.post("/payments/wompi/webhook", json=payload)
    assert response.status_code == 200

    updated = client.get(f"/orders/{order['order_number']}", params={"email": "comprador@example.com"})
    assert updated.json()["payment_status"] == "approved"
    assert updated.json()["status"] == "paid"


def test_wompi_webhook_rejects_bad_signature(client):
    payload = {
        "event": "transaction.updated",
        "data": {"transaction": {"id": "x", "status": "APPROVED", "reference": "JG-does-not-matter"}},
        "signature": {"properties": ["transaction.id"], "checksum": "not-the-real-checksum"},
        "timestamp": 1700000000,
    }
    response = client.post("/payments/wompi/webhook", json=payload)
    assert response.status_code == 401


def test_mercadopago_create_preference(monkeypatch):
    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"id": "pref-123", "init_point": "https://mercadopago.com/checkout/pref-123"}

    def _fake_post(*args, **kwargs):
        return _FakeResponse()

    monkeypatch.setattr("services.mercadopago_service.httpx.post", _fake_post)

    result = mercadopago_service.create_preference(
        order_number="JG-20260101-ABC123",
        items=[{"title": "Oud Royal", "quantity": 1, "unit_price": 350000.0}],
        notification_url="https://api.jgparfums.com/payments/mercadopago/webhook",
        back_url="https://jgparfums.com/pedido-confirmado.html",
    )
    assert result["checkout_url"] == "https://mercadopago.com/checkout/pref-123"
    assert result["reference"] == "JG-20260101-ABC123"


def test_mercadopago_webhook_signature_roundtrip():
    manifest = "id:123;request-id:req-1;ts:1700000000;"
    v1 = hmac.new(b"test_mp_secret", manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    x_signature = f"ts=1700000000,v1={v1}"

    assert mercadopago_service.verify_webhook_signature(x_signature, "req-1", "123") is True
    assert mercadopago_service.verify_webhook_signature("ts=1700000000,v1=wrong", "req-1", "123") is False


def test_wompi_integrity_signature_is_deterministic():
    sig_a = wompi_service.build_integrity_signature("JG-1", 100000)
    sig_b = wompi_service.build_integrity_signature("JG-1", 100000)
    sig_c = wompi_service.build_integrity_signature("JG-1", 200000)
    assert sig_a == sig_b
    assert sig_a != sig_c
