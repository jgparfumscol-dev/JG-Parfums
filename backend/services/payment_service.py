"""Punto único donde un evento de pago (de cualquier proveedor) actualiza un Order.

Las rutas de webhook normalizan el payload de su proveedor a
{reference, status, transaction_id} y llaman a apply_payment_update() acá.
Así agregar un tercer proveedor no toca la lógica de negocio, solo un parser nuevo.
"""

import logging

from sqlalchemy.orm import Session

from models.order import Order, OrderStatus, PaymentStatus
from services.email_service import email_pago_aprobado

logger = logging.getLogger("jg_parfums.payments")

_WOMPI_STATUS_MAP = {
    "APPROVED": PaymentStatus.approved,
    "DECLINED": PaymentStatus.declined,
    "VOIDED": PaymentStatus.declined,
    "ERROR": PaymentStatus.declined,
}

_MERCADOPAGO_STATUS_MAP = {
    "approved": PaymentStatus.approved,
    "rejected": PaymentStatus.declined,
    "cancelled": PaymentStatus.declined,
    "refunded": PaymentStatus.refunded,
    "pending": PaymentStatus.pending,
    "in_process": PaymentStatus.pending,
}


def apply_payment_update(
    db: Session, order_number: str, provider_status: str, transaction_id: str, provider: str
) -> Order | None:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if order is None:
        logger.warning("Webhook de %s referencia un pedido inexistente: %s", provider, order_number)
        return None

    status_map = _WOMPI_STATUS_MAP if provider == "wompi" else _MERCADOPAGO_STATUS_MAP
    new_status = status_map.get(provider_status)
    if new_status is None:
        logger.info("Estado de pago %s sin mapear para %s", provider_status, provider)
        return order

    already_approved = order.payment_status == PaymentStatus.approved
    order.payment_status = new_status
    order.payment_reference = transaction_id
    if new_status == PaymentStatus.approved:
        order.status = OrderStatus.paid
    elif new_status == PaymentStatus.declined and order.status == OrderStatus.pending:
        order.status = OrderStatus.cancelled

    db.commit()
    db.refresh(order)

    if new_status == PaymentStatus.approved and not already_approved:
        email_pago_aprobado(order.guest_email, order.order_number)

    return order
