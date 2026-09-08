import logging
import os

import httpx

logger = logging.getLogger("jg_parfums.email")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "JG Parfums <pedidos@jgparfums.com>")
RESEND_URL = "https://api.resend.com/emails"


def send_email(to: str, subject: str, html: str) -> bool:
    """Envío centralizado. Si el proveedor cambia, solo se toca esta función."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY no configurada, email a %s no enviado", to)
        return False
    try:
        response = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": EMAIL_FROM, "to": [to], "subject": subject, "html": html},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except httpx.HTTPError:
        logger.exception("Fallo enviando email a %s", to)
        return False


def email_bienvenida(to: str, full_name: str) -> bool:
    html = f"""
    <p>Hola {full_name},</p>
    <p>Tu cuenta en JG Parfums quedó creada. Ya puedes ver tu historial de pedidos
    cuando quieras.</p>
    """
    return send_email(to, "Bienvenido a JG Parfums", html)


def email_confirmacion_pedido(to: str, order_number: str, total: int) -> bool:
    html = f"""
    <p>Recibimos tu pedido <strong>{order_number}</strong> por un total de
    ${total:,} COP.</p>
    <p>Te avisamos apenas confirmemos el pago.</p>
    """
    return send_email(to, f"Pedido {order_number} recibido", html)


def email_pago_aprobado(to: str, order_number: str) -> bool:
    html = f"""
    <p>Tu pago del pedido <strong>{order_number}</strong> quedó confirmado.
    Ya empezamos a preparar tu envío.</p>
    """
    return send_email(to, f"Pago confirmado - pedido {order_number}", html)


def email_reset_password(to: str, reset_url: str) -> bool:
    html = f"""
    <p>Solicitaste restablecer tu contraseña.</p>
    <p><a href="{reset_url}">Haz clic aquí para elegir una nueva contraseña</a>.
    Este enlace vence en una hora.</p>
    <p>Si no fuiste tú, ignora este correo.</p>
    """
    return send_email(to, "Restablecer tu contraseña - JG Parfums", html)
