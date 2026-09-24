import logging
import os

import httpx

logger = logging.getLogger("jg_parfums.chat")

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "")
N8N_WEBHOOK_SECRET = os.environ.get("N8N_WEBHOOK_SECRET", "")


class ChatServiceError(Exception):
    """El webhook de n8n no está configurado, no respondió o devolvió algo
    irreconocible — el router la traduce a un 502/503 con mensaje genérico."""


def send_to_n8n(message: str, session_id: str, context: dict) -> str:
    """Reenvía el mensaje al workflow de n8n (Webhook + Respond to Webhook,
    ver el nodo de memoria/AI Agent para el historial por session_id) y
    devuelve el texto de la respuesta. El contexto del usuario (si hay
    sesión activa) ya viene resuelto por el router — acá nunca se manda el
    JWT, solo datos ya autorizados, para que n8n no pueda actuar como el
    usuario ni necesite saber nada de nuestro esquema de auth.
    """
    if not N8N_WEBHOOK_URL:
        raise ChatServiceError("N8N_WEBHOOK_URL no configurada")

    headers = {"X-Webhook-Secret": N8N_WEBHOOK_SECRET} if N8N_WEBHOOK_SECRET else {}
    try:
        response = httpx.post(
            N8N_WEBHOOK_URL,
            headers=headers,
            json={"message": message, "session_id": session_id, "context": context},
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
