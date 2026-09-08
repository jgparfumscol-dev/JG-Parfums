import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from database import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"


class PaymentProvider(str, enum.Enum):
    wompi = "wompi"
    mercado_pago = "mercado_pago"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    declined = "declined"
    refunded = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String, unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    guest_email = Column(String, nullable=False)
    guest_name = Column(String, nullable=False)
    guest_phone = Column(String, nullable=False)

    shipping_address = Column(String, nullable=False)
    shipping_city = Column(String, nullable=False)
    shipping_notes = Column(String, nullable=True)

    subtotal = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)

    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.pending)
    payment_provider = Column(SQLEnum(PaymentProvider), nullable=True)
    payment_status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    payment_reference = Column(String, nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
