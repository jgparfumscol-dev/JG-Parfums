from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_variant_id = Column(
        Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )

    # snapshot en el momento de la compra: el precio/nombre del producto puede
    # cambiar después y el pedido histórico no debe reflejar ese cambio.
    product_name = Column(String, nullable=False)
    size_ml = Column(Integer, nullable=True)  # tamaño comprado: null = frasco completo del producto
    unit_price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    variant = relationship("ProductVariant")
