"""Integración con Mercado Pago (Checkout Pro).

Referencia: https://www.mercadopago.com.co/developers/es/docs/checkout-pro
- Se crea una "preferencia" con los items del pedido; MP devuelve un init_point
  al que se redirige al comprador.
- El webhook trae solo el id del recurso. La recomendación oficial de MP es
  siempre volver a consultar el pago por su id en la API en vez de confiar en
  el cuerpo del webhook, porque el payload de la notificación no está firmado
  de forma consistente entre integraciones antiguas y nuevas.
- Cuando el webhook sí trae el header X-Signature (integraciones nuevas), se
  valida con el secret del webhook antes de siquiera mirar el body.
"""

import hashlib
import hmac
import logging
import os

import httpx

logger = logging.getLogger("jg_parfums.mercadopago")

MP_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
MP_WEBHOOK_SECRET = os.environ.get("MERCADOPAGO_WEBHOOK_SECRET", "")
MP_API_BASE = "https://api.mercadopago.com"


def create_preference(order_number: str, items: list[dict], notification_url: str, back_url: str) -> dict:
    """items: [{"title": str, "quantity": int, "unit_price": float}, ...]"""
    response = httpx.post(
        f"{MP_API_BASE}/checkout/preferences",
        headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
        json={
            "items": items,
            "external_reference": order_number,
            "notification_url": notification_url,
            "back_urls": {
                "success": back_url,
                "pending": back_url,
                "failure": back_url,
            },
            "auto_return": "approved",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "provider": "mercado_pago",
        "reference": order_number,
        "preference_id": data["id"],
        "checkout_url": data["init_point"],
    }


def verify_webhook_signature(x_signature: str | None, x_request_id: str | None, data_id: str) -> bool:
    if not MP_WEBHOOK_SECRET:
        logger.warning("MERCADOPAGO_WEBHOOK_SECRET no configurado, se omite verificación")
        return False
    if not x_signature:
        return False

    parts = dict(item.split("=", 1) for item in x_signature.split(",") if "=" in item)
    ts = parts.get("ts")
    v1 = parts.get("v1")
    if not ts or not v1:
        return False

    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(MP_WEBHOOK_SECRET.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


def get_payment(payment_id: str) -> dict:
    """Vuelve a consultar el pago por id: nunca se confía solo en el body del webhook."""
    response = httpx.get(
        f"{MP_API_BASE}/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "reference": data.get("external_reference"),
        "status": data.get("status"),  # approved, pending, rejected, refunded
        "payment_id": data.get("id"),
    }
