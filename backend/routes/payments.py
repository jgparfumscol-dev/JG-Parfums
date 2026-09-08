import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from models.order import Order, OrderStatus, PaymentProvider
from schemas.payment import PaymentInitResponse
from services import mercadopago_service, wompi_service
from services.payment_service import apply_payment_update

logger = logging.getLogger("jg_parfums.payments")

router = APIRouter(prefix="/payments", tags=["payments"])

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8000")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080")


def _get_payable_order(order_number: str, db: Session) -> Order:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este pedido ya no admite pago")
    return order


@router.post("/wompi/webhook", status_code=status.HTTP_200_OK)
async def wompi_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    if not wompi_service.verify_webhook_signature(payload):
        logger.warning("Webhook de Wompi con firma inválida")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma inválida")

    event = wompi_service.parse_webhook_event(payload)
    if event is None:
        return {"received": True}

    apply_payment_update(
        db,
        order_number=event["reference"],
        provider_status=event["status"],
        transaction_id=event["transaction_id"],
        provider="wompi",
    )
    return {"received": True}


@router.post("/mercadopago/webhook", status_code=status.HTTP_200_OK)
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    data_id = body.get("data", {}).get("id")
    if body.get("type") != "payment" or not data_id:
        return {"received": True}

    x_signature = request.headers.get("x-signature")
    x_request_id = request.headers.get("x-request-id")
    if not mercadopago_service.verify_webhook_signature(x_signature, x_request_id, str(data_id)):
        logger.warning("Webhook de Mercado Pago con firma inválida")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma inválida")

    # Nunca se confía en el status del body: se vuelve a consultar el pago por id.
    payment = mercadopago_service.get_payment(str(data_id))
    if payment["reference"]:
        apply_payment_update(
            db,
            order_number=payment["reference"],
            provider_status=payment["status"],
            transaction_id=str(payment["payment_id"]),
            provider="mercado_pago",
        )
    return {"received": True}


@router.post("/wompi/{order_number}", response_model=PaymentInitResponse)
def init_wompi_payment(order_number: str, db: Session = Depends(get_db)):
    order = _get_payable_order(order_number, db)
    redirect_url = f"{FRONTEND_URL}/pedido-confirmado.html?order={order_number}"
    config = wompi_service.build_checkout_config(order.order_number, order.total, redirect_url)

    order.payment_provider = PaymentProvider.wompi
    db.commit()

    return PaymentInitResponse(
        provider=PaymentProvider.wompi,
        order_number=order.order_number,
        reference=config["reference"],
        public_key=config["public_key"],
        integrity_signature=config["signature_integrity"],
        amount=order.total,
    )


@router.post("/mercadopago/{order_number}", response_model=PaymentInitResponse)
def init_mercadopago_payment(order_number: str, db: Session = Depends(get_db)):
    order = _get_payable_order(order_number, db)
    items = [
        {"title": item.product_name, "quantity": item.quantity, "unit_price": float(item.unit_price)}
        for item in order.items
    ]
    result = mercadopago_service.create_preference(
        order_number=order.order_number,
        items=items,
        notification_url=f"{BACKEND_URL}/payments/mercadopago/webhook",
        back_url=f"{FRONTEND_URL}/pedido-confirmado.html?order={order_number}",
    )

    order.payment_provider = PaymentProvider.mercado_pago
    db.commit()

    return PaymentInitResponse(
        provider=PaymentProvider.mercado_pago,
        order_number=order.order_number,
        checkout_url=result["checkout_url"],
        reference=result["reference"],
        amount=order.total,
    )
