import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin, get_optional_user
from models.order import Order
from models.order_item import OrderItem
from models.product import Product
from models.user import User
from schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from services.email_service import email_confirmacion_pedido

router = APIRouter(prefix="/orders", tags=["orders"])


def _generate_order_number() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"JG-{stamp}-{secrets.token_hex(3).upper()}"


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    order_items: list[OrderItem] = []
    subtotal = 0

    # Se valida y descuenta stock en la misma transacción que crea el pedido:
    # dos checkouts concurrentes sobre el último frasco no deben poder venderlo dos veces.
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id, Product.is_active.is_(True)).first()
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Producto {item.product_id} no disponible"
            )
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para {product.name}",
            )
        product.stock -= item.quantity
        subtotal += product.price * item.quantity
        order_items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=item.quantity,
            )
        )

    order = Order(
        order_number=_generate_order_number(),
        user_id=user.id if user else None,
        guest_email=payload.guest_email,
        guest_name=payload.guest_name,
        guest_phone=payload.guest_phone,
        shipping_address=payload.shipping_address,
        shipping_city=payload.shipping_city,
        shipping_notes=payload.shipping_notes,
        subtotal=subtotal,
        total=subtotal,
        items=order_items,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    email_confirmacion_pedido(order.guest_email, order.order_number, order.total)
    return order


@router.get("/me", response_model=list[OrderResponse])
def list_my_orders(db: Session = Depends(get_db), user: User = Depends(get_optional_user)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()


@router.get("/{order_number}", response_model=OrderResponse)
def get_order(
    order_number: str,
    email: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

    is_owner = user is not None and order.user_id == user.id
    is_admin = user is not None and user.is_admin
    is_verified_guest = email is not None and email.lower() == order.guest_email.lower()
    if not (is_owner or is_admin or is_verified_guest):
        # mismo 404 que "no existe": no confirmar la existencia del pedido a quien no lo pidió
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

    return order


@router.get("", response_model=list[OrderResponse])
def list_all_orders(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return db.query(Order).order_by(Order.created_at.desc()).all()


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order
