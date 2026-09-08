from pydantic import BaseModel

from models.order import PaymentProvider


class PaymentInitResponse(BaseModel):
    provider: PaymentProvider
    order_number: str
    checkout_url: str | None = None  # Wompi Web Checkout / Mercado Pago init_point
    reference: str  # referencia que el proveedor devuelve en el webhook
    public_key: str | None = None  # para armar el widget embebido en el frontend
    integrity_signature: str | None = None  # firma de Wompi, calculada solo en el backend
    amount: int
    currency: str = "COP"


class WompiWebhookEvent(BaseModel):
    event: str
    data: dict
    signature: dict
    timestamp: int


class MercadoPagoWebhookEvent(BaseModel):
    type: str
    data: dict
