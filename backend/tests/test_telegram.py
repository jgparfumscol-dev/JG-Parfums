import hashlib
import logging

import httpx
import pytest

from models.order import Order
from services import telegram_service

TOKEN = "123456:SECRET-token_ABC"
CHAT_ID = "987654"


class _Recorder:
    """Reemplaza httpx.post del servicio: guarda las llamadas, nunca sale a internet."""

    def __init__(self):
        self.calls = []
        self.error = None
        self.status_code = 200

    def __call__(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        if self.error:
            raise self.error
        request = httpx.Request("POST", url)
        return httpx.Response(
            self.status_code, json={"ok": self.status_code == 200, "description": "Bad Request: chat not found"}, request=request
        )


@pytest.fixture
def telegram(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", CHAT_ID)
    recorder = _Recorder()
    monkeypatch.setattr("services.telegram_service.httpx.post", recorder)
    return recorder


def _create_product(client, admin_headers, name="Oud_Royal *Edition*", stock=5, price=350000):
    payload = {
        "slug": "oud-royal",
        "name": name,
        "description": "Amaderado oriental, para la noche.",
        "size_ml": 100,
        "price": price,
        "stock": stock,
    }
    return client.post("/products", json=payload, headers=admin_headers).json()


def _create_order(client, product_id, variant_id=None, headers=None, **extra):
    payload = {
        "guest_email": "comprador@example.com",
        "guest_name": "Comprador Test",
        "guest_phone": "3001234567",
        "shipping_address": "Calle 1 # 2-3",
        "shipping_city": "Bogotá",
        "items": [{"product_id": product_id, "variant_id": variant_id, "quantity": 2}],
        **extra,
    }
    return client.post("/orders", json=payload, headers=headers or {}).json()


def _wompi_payload(order, status="APPROVED"):
    transaction = {
        "id": "txn-123",
        "status": status,
        "reference": order["order_number"],
        "amount_in_cents": order["total"] * 100,
    }
    properties = ["transaction.id", "transaction.status", "transaction.amount_in_cents"]
    concatenated = "".join(str(transaction[prop.split(".")[1]]) for prop in properties)
    concatenated += "1700000000test_events_secret"
    return {
        "event": "transaction.updated",
        "data": {"transaction": transaction},
        "signature": {"properties": properties, "checksum": hashlib.sha256(concatenated.encode()).hexdigest()},
        "timestamp": 1700000000,
    }


def _pay_wompi(client, order, status="APPROVED"):
    return client.post("/payments/wompi/webhook", json=_wompi_payload(order, status))


def test_notifies_when_wompi_payment_is_approved(client, admin_headers, telegram):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"], shipping_notes="Portería, apto 501")

    response = _pay_wompi(client, order)

    assert response.status_code == 200
    assert len(telegram.calls) == 1
    call = telegram.calls[0]
    assert call["url"] == f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    assert call["timeout"] == 10
    assert call["json"]["chat_id"] == CHAT_ID
    assert "parse_mode" not in call["json"]
    text = call["json"]["text"]
    assert f"Pedido pagado #{order['order_number']}" in text
    assert "Total: $700.000 COP (pasarela: Wompi)" in text
    assert "- Oud_Royal *Edition* — Frasco 100 ml × 2" in text
    assert "Cliente: Comprador Test" in text
    assert "Teléfono: 3001234567" in text
    assert "Ciudad: Bogotá" in text
    assert "Dirección: Calle 1 # 2-3" in text
    assert "Notas de entrega: Portería, apto 501" in text
    assert "Envío: $0 COP" in text


def test_message_shows_decant_presentation_and_shipping_cost(client, admin_headers, telegram):
    client.put("/settings", json={"shipping_cost": 12500}, headers=admin_headers)
    product = _create_product(client, admin_headers, name="Oud Royal")
    variant = client.post(
        f"/products/{product['id']}/variants", json={"size_ml": 10, "price": 80000, "stock": 10}, headers=admin_headers
    ).json()
    order = _create_order(client, product["id"], variant_id=variant["id"])

    _pay_wompi(client, order)

    text = telegram.calls[0]["json"]["text"]
    assert "- Oud Royal — Decant 10 ml × 2" in text
    assert "decant 10ml" not in text
    assert "Envío: $12.500 COP" in text
    assert "Total: $172.500 COP" in text
    assert "Notas de entrega" not in text


def test_notifies_for_registered_user_purchase(client, admin_headers, admin_token, telegram):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"], headers={"Authorization": f"Bearer {admin_token}"})

    _pay_wompi(client, order)

    assert len(telegram.calls) == 1
    assert "Cliente: Comprador Test" in telegram.calls[0]["json"]["text"]


def test_notifies_when_mercadopago_payment_is_approved(client, admin_headers, telegram, monkeypatch):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])
    monkeypatch.setattr("routes.payments.mercadopago_service.verify_webhook_signature", lambda *a: True)
    monkeypatch.setattr(
        "routes.payments.mercadopago_service.get_payment",
        lambda payment_id: {"reference": order["order_number"], "status": "approved", "payment_id": payment_id},
    )

    response = client.post("/payments/mercadopago/webhook", json={"type": "payment", "data": {"id": "555"}})

    assert response.status_code == 200
    assert len(telegram.calls) == 1
    assert "pasarela: Mercado Pago" in telegram.calls[0]["json"]["text"]


def test_repeated_webhook_notifies_only_once(client, admin_headers, telegram, db):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])

    assert _pay_wompi(client, order).status_code == 200
    assert _pay_wompi(client, order).status_code == 200
    assert _pay_wompi(client, order).status_code == 200

    assert len(telegram.calls) == 1
    stored = db.query(Order).filter(Order.order_number == order["order_number"]).first()
    assert stored.notified_at is not None


def test_notified_at_prevents_a_second_notification_even_if_payment_status_is_reset(
    client, admin_headers, telegram, db
):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])
    _pay_wompi(client, order)

    stored = db.query(Order).filter(Order.order_number == order["order_number"]).first()
    stored.payment_status = "pending"  # p. ej. un reintento fuera de orden
    db.commit()
    _pay_wompi(client, order)

    assert len(telegram.calls) == 1


def test_does_not_notify_when_payment_is_declined(client, admin_headers, telegram, db):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])

    response = _pay_wompi(client, order, status="DECLINED")

    assert response.status_code == 200
    assert telegram.calls == []
    stored = db.query(Order).filter(Order.order_number == order["order_number"]).first()
    assert stored.notified_at is None


def test_does_not_notify_when_mercadopago_payment_is_pending(client, admin_headers, telegram, monkeypatch):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])
    monkeypatch.setattr("routes.payments.mercadopago_service.verify_webhook_signature", lambda *a: True)
    monkeypatch.setattr(
        "routes.payments.mercadopago_service.get_payment",
        lambda payment_id: {"reference": order["order_number"], "status": "in_process", "payment_id": payment_id},
    )

    client.post("/payments/mercadopago/webhook", json={"type": "payment", "data": {"id": "555"}})

    assert telegram.calls == []


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectTimeout("timeout"),
        httpx.ConnectError("sin red"),
        RuntimeError("cualquier cosa"),
    ],
)
def test_telegram_failure_does_not_break_order_or_webhook(client, admin_headers, telegram, error):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])
    telegram.error = error

    response = _pay_wompi(client, order)

    assert response.status_code == 200
    updated = client.get(f"/orders/{order['order_number']}", params={"email": "comprador@example.com"}).json()
    assert updated["status"] == "paid"
    assert updated["payment_status"] == "approved"


@pytest.mark.parametrize("failure", ["timeout", "http_500"])
def test_order_stays_paid_and_marked_notified_when_the_send_fails_and_is_not_retried(
    client, admin_headers, telegram, db, failure
):
    """Se marca antes de enviar: si el POST falla, notified_at queda y no hay reintento."""
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])
    if failure == "timeout":
        telegram.error = httpx.ReadTimeout("timeout")
    else:
        telegram.status_code = 500

    assert _pay_wompi(client, order).status_code == 200
    assert len(telegram.calls) == 1  # el envío se intentó

    stored = db.query(Order).filter(Order.order_number == order["order_number"]).first()
    assert stored.status.value == "paid"
    assert stored.payment_status.value == "approved"
    assert stored.notified_at is not None  # sin revertir pese al fallo

    # la pasarela repite el webhook: no hay segundo intento
    assert _pay_wompi(client, order).status_code == 200
    assert len(telegram.calls) == 1
    db.expire_all()
    assert stored.notified_at is not None
    assert stored.status.value == "paid"


def test_telegram_http_error_status_does_not_break_order(client, admin_headers, telegram):
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])
    telegram.status_code = 400

    response = _pay_wompi(client, order)

    assert response.status_code == 200
    updated = client.get(f"/orders/{order['order_number']}", params={"email": "comprador@example.com"}).json()
    assert updated["status"] == "paid"


@pytest.mark.parametrize("missing", ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "both"])
def test_missing_variables_do_nothing_and_do_not_break_order(client, admin_headers, telegram, monkeypatch, missing, db):
    if missing in ("TELEGRAM_BOT_TOKEN", "both"):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN")
    if missing in ("TELEGRAM_CHAT_ID", "both"):
        monkeypatch.delenv("TELEGRAM_CHAT_ID")
    product = _create_product(client, admin_headers)
    order = _create_order(client, product["id"])

    response = _pay_wompi(client, order)

    assert response.status_code == 200
    assert telegram.calls == []
    updated = client.get(f"/orders/{order['order_number']}", params={"email": "comprador@example.com"}).json()
    assert updated["status"] == "paid"
    stored = db.query(Order).filter(Order.order_number == order["order_number"]).first()
    assert stored.notified_at is None  # no se marcó como avisado algo que no se avisó


def test_token_never_appears_in_logs_on_failures(client, admin_headers, telegram, caplog):
    caplog.set_level(logging.DEBUG)
    product = _create_product(client, admin_headers)

    for error, status_code in [(httpx.ConnectError(f"fallo en {TOKEN}"), 200), (None, 401)]:
        telegram.error = error
        telegram.status_code = status_code
        order = _create_order(client, product["id"])
        assert _pay_wompi(client, order).status_code == 200

    assert TOKEN not in caplog.text
    assert "Telegram" in caplog.text  # sí se dejó registro del fallo


def test_token_is_redacted_from_httpx_request_logs(telegram, caplog):
    caplog.set_level(logging.DEBUG)
    url = telegram_service.TELEGRAM_API_URL.format(token=TOKEN)

    logging.getLogger("httpx").info('HTTP Request: %s %s "%s"', "POST", httpx.URL(url), "HTTP/1.1 200 OK")

    assert TOKEN not in caplog.text
    assert "HTTP Request: POST" in caplog.text


def test_token_is_redacted_from_unhandled_exception_tracebacks(monkeypatch, caplog):
    """Si algo escapara del BackgroundTask, uvicorn registra el traceback completo;
    el mensaje de la excepción de httpx trae la URL (con el token)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TOKEN)
    caplog.set_level(logging.DEBUG)
    url = telegram_service.TELEGRAM_API_URL.format(token=TOKEN)
    response = httpx.Response(500, request=httpx.Request("POST", url))
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        assert TOKEN in str(exc)  # el riesgo es real: la excepción sí lleva el token
        logging.getLogger("uvicorn.error").error("Exception in ASGI application", exc_info=exc)

    assert TOKEN not in caplog.text
    assert "Exception in ASGI application" in caplog.text
    assert "HTTPStatusError" in caplog.text


def test_send_never_lets_an_exception_with_the_token_escape(monkeypatch, caplog):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", CHAT_ID)
    caplog.set_level(logging.DEBUG)
    url = telegram_service.TELEGRAM_API_URL.format(token=TOKEN)

    def _boom(*args, **kwargs):
        raise httpx.ConnectError(f"fallo conectando a {url}")

    monkeypatch.setattr("services.telegram_service.httpx.post", _boom)

    assert telegram_service.send_telegram_message("hola") is False
    assert TOKEN not in caplog.text


def test_missing_variables_only_log_a_warning(monkeypatch, caplog):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    assert telegram_service.send_telegram_message("hola") is False
    assert "no configuradas" in caplog.text


def test_format_cop_uses_dot_as_thousands_separator():
    assert telegram_service.format_cop(0) == "$0"
    assert telegram_service.format_cop(950) == "$950"
    assert telegram_service.format_cop(1250000) == "$1.250.000"
