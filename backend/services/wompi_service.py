"""Integración con Wompi (Web Checkout / Widget).

Referencia: https://docs.wompi.co/
- El "checkout de widget" se arma en el frontend con un formulario firmado.
  La firma de integridad evita que alguien manipule el monto desde el navegador.
- Los webhooks ("eventos") traen su propio checksum, calculado con el "events secret"
  (distinto de la llave privada de la API).
"""

import hashlib
import logging
import os

logger = logging.getLogger("jg_parfums.wompi")

WOMPI_PUBLIC_KEY = os.environ.get("WOMPI_PUBLIC_KEY", "")
WOMPI_INTEGRITY_SECRET = os.environ.get("WOMPI_INTEGRITY_SECRET", "")
WOMPI_EVENTS_SECRET = os.environ.get("WOMPI_EVENTS_SECRET", "")


def build_integrity_signature(reference: str, amount_in_cents: int, currency: str = "COP") -> str:
    raw = f"{reference}{amount_in_cents}{currency}{WOMPI_INTEGRITY_SECRET}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_checkout_config(order_number: str, total_cop: int, redirect_url: str) -> dict:
    amount_in_cents = total_cop * 100
    return {
        "provider": "wompi",
        "public_key": WOMPI_PUBLIC_KEY,
        "currency": "COP",
        "amount_in_cents": amount_in_cents,
        "reference": order_number,
        "signature_integrity": build_integrity_signature(order_number, amount_in_cents),
        "redirect_url": redirect_url,
    }


def verify_webhook_signature(payload: dict) -> bool:
    """Valida el checksum que Wompi manda en payload['signature'].

    payload['signature']['properties'] lista las claves (ej. "transaction.id",
    "transaction.status", "transaction.amount_in_cents") cuyos valores, concatenados
    en ese orden junto con el timestamp y el events secret, deben producir el checksum.
    """
    try:
        signature = payload["signature"]
        properties: list[str] = signature["properties"]
        checksum = signature["checksum"]
        timestamp = payload["timestamp"]
    except KeyError:
        logger.warning("Webhook de Wompi con formato inesperado")
        return False

    data = payload.get("data", {})
    concatenated = ""
    for prop_path in properties:
        value = data
        for part in prop_path.split("."):  # ej. "transaction.id" navega data["transaction"]["id"]
            value = value.get(part) if isinstance(value, dict) else None
        concatenated += str(value)
    concatenated += f"{timestamp}{WOMPI_EVENTS_SECRET}"

    expected = hashlib.sha256(concatenated.encode("utf-8")).hexdigest()
    return expected == checksum


def parse_webhook_event(payload: dict) -> dict | None:
    """Devuelve {reference, status, transaction_id} o None si el evento no es de transacción."""
    if payload.get("event") != "transaction.updated":
        return None
    transaction = payload.get("data", {}).get("transaction", {})
    return {
        "reference": transaction.get("reference"),
        "status": transaction.get("status"),  # APPROVED, DECLINED, VOIDED, ERROR
        "transaction_id": transaction.get("id"),
    }
