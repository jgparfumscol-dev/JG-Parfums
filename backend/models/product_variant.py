from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class ProductVariant(Base):
    """Decant: el mismo perfume del Product padre, fraccionado en 5ml o 10ml.

    Precio y stock son propios de la presentación — un decant no descuenta
    del stock del frasco completo, se prepara y se cuenta aparte (decisión
    de negocio: más simple de operar que fraccionar mililitros del frasco).
    """

    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    size_ml = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)  # COP, pesos enteros
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    # Foto propia de la presentación (ej. el frasco de 5ml junto a su caja).
    # Opcional: si no se define, la ficha sigue mostrando la galería del producto.
    image_url = Column(String, nullable=True)

    product = relationship("Product", back_populates="variants")
