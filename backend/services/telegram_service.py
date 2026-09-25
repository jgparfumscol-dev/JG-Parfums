"""Aviso por Telegram al equipo cuando un pedido pasa a pagado.

Todo lo de acá está pensado para no romper nunca el flujo del webhook de pago:
sin variables de entorno no hace nada, y cualquier fallo de Telegram queda solo
en el log. El token va en la URL de la API de Telegram, así que jamás se loguea
(ni directo ni dentro del mensaje de una excepción de httpx, que incluye la URL).
"""

import logging
import os
from datetime import datetime, timezone

import httpx
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from models.order import Order

logger = logging.getLogger("jg_parfums.telegram")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
# Telegram rechaza mensajes de más de 4096 caracteres.
MAX_MESSAGE_LENGTH = 4000

_PROVIDER_LABELS = {"wompi": "Wompi", "mercado_pago": "Mercado Pago"}
_DECANT_MARKER = " — decant "


def _credentials() -> tuple[str, str]:
    return (
        os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
        os.environ.get("TELEGRAM_CHAT_ID", "").strip(),
    )


def is_configured() -> bool:
    token, chat_id = _credentials()
    return bool(token and chat_id)


class _RedactTokenFilter(logging.Filter):
    """httpx loguea a INFO cada request con la URL completa, y ahí va el token.
    También cubre el traceback de una excepción sin manejar (ej. uvicorn.error
    con "Exception in ASGI application"), cuyo mensaje puede traer esa URL."""

    def filter(self, record: logging.LogRecord) -> bool:
        token, _ = _credentials()
        if not token:
            return True
        try:
            message = record.getMessage()
            if token in message:
                record.msg = message.replace(token, "***")
                record.args = ()
            if record.exc_info and not record.exc_text:
                record.exc_text = logging.Formatter().formatException(record.exc_info)
            if record.exc_text and token in record.exc_text:
                record.exc_text = record.exc_text.replace(token, "***")
            if record.stack_info and token in record.stack_info:
                record.stack_info = record.stack_info.replace(token, "***")
        except Exception:
            pass
        return True


for _name in ("httpx", "httpcore", "uvicorn", "uvicorn.error", "starlette", "fastapi"):
    logging.getLogger(_name).addFilter(_RedactTokenFilter())


def format_cop(amount: int) -> str:
    return "$" + f"{amount:,}".replace(",", ".")


def _item_line(item) -> str:
    name = item.product_name
    is_decant = item.product_variant_id is not None or _DECANT_MARKER in name
    if is_decant:
        name = name.split(_DECANT_MARKER)[0]
        presentation = f"Decant {item.size_ml} ml" if item.size_ml else "Decant"
    else:
        presentation = f"Frasco {item.size_ml} ml" if item.size_ml else "Frasco"
    return f"- {name} — {presentation} × {item.quantity}"


def build_paid_order_message(order: Order, provider: str) -> str:
    """Texto plano, sin parse_mode: nombres con _ * [ ] etc. no pueden romper el envío."""
    lines = [
        f"Pedido pagado #{order.order_number}",
        f"Total: {format_cop(order.total)} COP (pasarela: {_PROVIDER_LABELS.get(provider, provider)})",
        "",
        "Productos:",
        *(_item_line(item) for item in order.items),
        "",
        f"Cliente: {order.guest_name}",
        f"Teléfono: {order.guest_phone}",
        f"Ciudad: {order.shipping_city}",
        f"Dirección: {order.shipping_address}",
    ]
    if order.shipping_notes:
        lines.append(f"Notas de entrega: {order.shipping_notes}")
    lines.append(f"Envío: {format_cop(order.shipping_cost)} COP")
    return "\n".join(lines)[:MAX_MESSAGE_LENGTH]


def send_telegram_message(text: str) -> bool:
    """Devuelve True si Telegram aceptó el mensaje. Nunca lanza."""
    token, chat_id = _credentials()
    if not token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID no configuradas, aviso de Telegram no enviado")
        return False
    try:
        response = httpx.post(
            TELEGRAM_API_URL.format(token=token),
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except httpx.HTTPStatusError as exc:
        # Sin logger.exception ni str(exc): ambos traen la URL, o sea el token.
        try:
            detail = str(exc.response.json().get("description", ""))[:200]
        except Exception:
            detail = ""
        logger.error("Telegram respondió %s: %s", exc.response.status_code, detail)
        return False
    except Exception as exc:
        logger.error("Fallo enviando aviso a Telegram (%s)", type(exc).__name__)
        return False


def notify_order_paid(
    db: Session, order: Order, provider: str, background_tasks: BackgroundTasks | None = None
) -> None:
    """Avisa UNA sola vez por pedido: el UPDATE condicional sobre notified_at
    hace de cerrojo, así que dos webhooks repetidos (o simultáneos) no duplican
    el aviso. Nunca lanza: si algo falla solo se loguea."""
    try:
        if not is_configured():
            logger.warning("Telegram sin configurar, pedido %s sin avisar", order.order_number)
            return

        claimed = (
            db.query(Order)
            .filter(Order.id == order.id, Order.notified_at.is_(None))
            .update({"notified_at": datetime.now(timezone.utc)}, synchronize_session=False)
        )
        db.commit()
        if not claimed:
            return

        # El texto se arma acá, con la sesión abierta: la tarea de fondo no toca la BD.
        text = build_paid_order_message(order, provider)
        if background_tasks is not None:
            background_tasks.add_task(send_telegram_message, text)
        else:
            send_telegram_message(text)
    except Exception as exc:
        db.rollback()
        logger.error("No se pudo preparar el aviso de Telegram del pedido (%s)", type(exc).__name__)
