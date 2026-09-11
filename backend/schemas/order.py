from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from models.order import OrderStatus, PaymentProvider, PaymentStatus


class OrderItemCreate(BaseModel):
    product_id: int
    variant_id: int | None = None  # None = frasco completo; si no, decant de 5ml/10ml
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    """Payload de checkout. user_id se resuelve del JWT si viene autenticado, no de aquí."""

    guest_email: EmailStr
    guest_name: str = Field(min_length=1)
    guest_phone: str = Field(min_length=1)
    shipping_address: str = Field(min_length=1)
    shipping_city: str = Field(min_length=1)
    shipping_notes: str | None = None
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int | None
    product_variant_id: int | None
    product_name: str
    size_ml: int | None
    unit_price: int
    quantity: int

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    order_number: str
    guest_email: EmailStr
    guest_name: str
    guest_phone: str
    shipping_address: str
    shipping_city: str
    shipping_notes: str | None
    subtotal: int
    total: int
    status: OrderStatus
    payment_provider: PaymentProvider | None
    payment_status: PaymentStatus
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
