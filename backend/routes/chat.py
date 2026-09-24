from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from main import limiter
from middleware.auth import get_optional_user
from models.order import Order
from models.user import User
from schemas.chat import ChatMessageRequest, ChatMessageResponse
from services.chat_service import ChatServiceError, send_to_n8n

router = APIRouter(prefix="/chat", tags=["chat"])

# Cuántos pedidos recientes se le pasan a n8n como contexto cuando hay
# sesión activa — alcanza para "¿cómo va mi último pedido?" sin mandar el
# historial completo de cada mensaje.
_RECENT_ORDERS_LIMIT = 5


def _build_context(db: Session, user: User | None) -> dict:
    if user is None:
        return {"authenticated": False}

    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(_RECENT_ORDERS_LIMIT)
        .all()
    )
    return {
        "authenticated": True,
        "user_name": user.full_name,
        "user_email": user.email,
        "recent_orders": [
            {
                "order_number": o.order_number,
                "status": o.status.value,
                "payment_status": o.payment_status.value,
                "total": o.total,
                "created_at": o.created_at.isoformat(),
                "items": [f"{it.quantity}x {it.product_name}" for it in o.items],
            }
            for o in orders
        ],
    }


@router.post("/message", response_model=ChatMessageResponse)
@limiter.limit("20/minute")
def send_chat_message(
    request: Request,
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # El contexto (si hay sesión activa, nombre + pedidos recientes ya
    # resueltos acá) es lo único que sale hacia n8n — nunca el JWT del
    # usuario, así n8n no puede actuar en su nombre ni necesita saber nada
    # de nuestro esquema de auth.
    context = _build_context(db, user)
    try:
        reply = send_to_n8n(payload.message, payload.session_id, context)
    except ChatServiceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No pudimos conectar con el asistente. Intenta de nuevo en un momento.",
        )
    return ChatMessageResponse(reply=reply)
