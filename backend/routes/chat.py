from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from main import limiter
from middleware.auth import get_optional_user
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.user import User
from schemas.chat import ChatMessageRequest, ChatMessageResponse
from services.chat_catalog import build_catalog_context
from services.chat_service import ChatServiceError, send_to_n8n

router = APIRouter(prefix="/chat", tags=["chat"])

# Cuántos pedidos recientes se le pasan a n8n como contexto cuando hay
# sesión activa — alcanza para "¿cómo va mi último pedido?" sin mandar el
# historial completo de cada mensaje.
_RECENT_ORDERS_LIMIT = 5

# Tope de caracteres de customer_context — texto plano para el prompt de
# n8n, no hace falta (ni conviene, por costo/latencia del LLM) mandar más.
_MAX_CONTEXT_CHARS = 2000

# Estados internos del pedido (ver models/order.py, OrderStatus) a frases en
# español que un cliente entienda sin explicación — texto para el prompt de
# n8n, no para la UI del panel admin (que sigue mostrando el valor crudo).
_STATUS_ES = {
    OrderStatus.pending: "pendiente de pago",
    OrderStatus.paid: "pagado",
    OrderStatus.processing: "en preparación",
    OrderStatus.shipped: "enviado",
    OrderStatus.completed: "entregado",
    OrderStatus.cancelled: "cancelado",
}

_MESES_ES = (
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
)


def _format_date_es(dt) -> str:
    return f"{dt.day} {_MESES_ES[dt.month - 1]} {dt.year}"


def _format_cop(amount: int) -> str:
    return f"${amount:,}".replace(",", ".")


def _item_line(item: OrderItem) -> str:
    # product_variant_id sin valor = frasco completo; con valor = decant, y
    # en ese caso product_name ya trae "— decant Xml" (ver routes/orders.py,
    # create_order) así que no hace falta repetir la presentación.
    if item.product_variant_id is not None:
        return f"{item.quantity}x {item.product_name}"
    return f"{item.quantity}x {item.product_name} (frasco)"


def _format_order_line(order: Order) -> str:
    status_es = _STATUS_ES.get(order.status, order.status.value)
    items_str = "; ".join(_item_line(it) for it in order.items)
    return (
        f"Pedido {order.order_number} ({_format_date_es(order.created_at)}): {status_es}. "
        f"Productos: {items_str}. Total: {_format_cop(order.total)}."
    )


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = text[:max_chars]
    cut = head.rsplit("\n", 1)[0] if "\n" in head else head
    return cut.rstrip() + "…"


def build_customer_context(db: Session, user: User | None) -> tuple[str, bool]:
    """Arma el texto plano que se le manda a n8n con los pedidos del cliente
    (nunca por parámetros del body — el user_id sale únicamente del JWT ya
    resuelto por get_optional_user). Solo lo mínimo descrito en la tarea:
    número de pedido, fecha, estado en español, productos con presentación y
    cantidad, total. Nunca dirección, teléfono, correo, documento ni datos
    de pago — y ningún campo que no exista realmente en el modelo (ej. no
    hay número de guía/transportadora en Order todavía).

    Devuelve ("", False) sin sesión (o token inválido/expirado, que
    get_optional_user ya trata como visitante anónimo).
    """
    if user is None:
        return "", False

    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(_RECENT_ORDERS_LIMIT)
        .all()
    )
    if not orders:
        return "El cliente no tiene pedidos registrados todavía.", True

    text = "\n".join(_format_order_line(o) for o in orders)
    return _truncate(text, _MAX_CONTEXT_CHARS), True


@router.post("/message", response_model=ChatMessageResponse)
@limiter.limit("20/minute")
def send_chat_message(
    request: Request,
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # customer_context (si hay sesión activa, ya resuelto del lado del
    # servidor a partir del JWT) es lo único que sale hacia n8n sobre el
    # cliente — nunca el JWT en sí, así n8n no puede actuar en su nombre ni
    # necesita saber nada de nuestro esquema de auth.
    customer_context, is_logged_in = build_customer_context(db, user)
    # Catálogo público (clases y perfumes activos, ordenado según lo que el
    # cliente acaba de escribir) para que recomiende lo que de verdad hay.
    catalog_context = build_catalog_context(db, payload.message)
    try:
        reply = send_to_n8n(
            payload.message, payload.session_id, customer_context, is_logged_in, catalog_context
        )
    except ChatServiceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No pudimos conectar con el asistente. Intenta de nuevo en un momento.",
        )
    return ChatMessageResponse(reply=reply)
