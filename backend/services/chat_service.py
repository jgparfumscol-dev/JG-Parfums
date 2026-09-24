import logging
import os

import httpx

logger = logging.getLogger("jg_parfums.chat")


def _normalize_webhook_url(raw: str) -> str:
    """Tolera que se pegue solo el dominio (ej. "mi-n8n.up.railway.app",
    sin esquema) — httpx no acepta una URL sin http(s) al frente."""
    raw = (raw or "").strip()
    if raw and not raw.startswith(("http://", "https://")):
        return f"https://{raw}"
    return raw


N8N_WEBHOOK_URL = _normalize_webhook_url(os.environ.get("N8N_CHAT_WEBHOOK_URL", ""))
N8N_WEBHOOK_SECRET = os.environ.get("N8N_CHAT_WEBHOOK_SECRET", "")


class ChatServiceError(Exception):
    """El webhook de n8n no está configurado, no respondió o devolvió algo
    irreconocible — el router la traduce a un 502/503 con mensaje genérico."""


def send_to_n8n(message: str, session_id: str, customer_context: str, is_logged_in: bool) -> str:
    """Reenvía el mensaje al workflow de n8n (Webhook + Respond to Webhook,
    ver el nodo de memoria/AI Agent para el historial por session_id) y
    devuelve el texto de la respuesta.

    `customer_context` ya viene resuelto por el router como texto plano listo
    para el prompt (vacío si no hay sesión) — acá nunca se manda el JWT del
    usuario ni ningún dato sensible (dirección, teléfono, correo, documento,
    datos de pago), así n8n no puede actuar como el usuario ni necesita saber
    nada de nuestro esquema de auth. Ver routes/chat.py, build_customer_context.
    """
    if not N8N_WEBHOOK_URL:
        raise ChatServiceError("N8N_CHAT_WEBHOOK_URL no configurada")

    headers = {"X-Chat-Secret": N8N_WEBHOOK_SECRET} if N8N_WEBHOOK_SECRET else {}
    try:
        response = httpx.post(
            N8N_WEBHOOK_URL,
            headers=headers,
            json={
                "message": message,
                "session_id": session_id,
                "is_logged_in": is_logged_in,
                "customer_context": customer_context,
            },
            timeout=20,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Fallo llamando al webhook de n8n")
        raise ChatServiceError("no se pudo contactar a n8n") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise ChatServiceError("respuesta de n8n no es JSON") from exc

    # Acepta unos cuantos nombres de campo comunes en workflows de n8n
    # (Respond to Webhook con "reply" propio, o el output crudo de un nodo
    # AI Agent/Basic LLM Chain, que suele llamarse "output" o "text").
    reply = data.get("reply") or data.get("output") or data.get("text")
    if not reply or not isinstance(reply, str):
        raise ChatServiceError("respuesta de n8n sin un campo de texto reconocible (reply/output/text)")
    return reply
