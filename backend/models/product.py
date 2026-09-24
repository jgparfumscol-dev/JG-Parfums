from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from database import Base
from services.pricing import apply_discount

# Un producto puede estar en una, dos o más clases (antes category_id, una
# sola) — tabla puente sin columnas propias, ver la migración
# b8c9d0e1f2a3_products_many_to_many_categories para el backfill desde la
# columna vieja.
product_categories = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Product(Base):
    """Perfume original de nicho. Casi siempre una sola presentación (size_ml)."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    house = Column(String, nullable=True)  # casa/marca original del perfume
    description = Column(Text, nullable=False)
    concentration = Column(String, nullable=True)  # EDP, EDT, extrait de parfum
    size_ml = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)  # COP, pesos enteros (sin centavos)
    stock = Column(Integer, nullable=False, default=0)
    # Descuento en % (0–99) sobre el frasco y todos sus decants; 0 = sin descuento.
    discount_percent = Column(Integer, nullable=False, default=0, server_default="0")
    is_active = Column(Boolean, nullable=False, default=True)
    # Producto que se muestra en la ficha "destacada" del home (diagrama de
    # notas). Solo uno puede estar marcado a la vez — se hace cumplir en la
    # ruta, no con una constraint de DB (ver update_product).
    is_featured = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.position",
    )
    variants = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.size_ml",
    )
    notes = relationship(
        "ProductNote",
        cascade="all, delete-orphan",
        order_by="ProductNote.position",
    )
    detail_sections = relationship(
        "ProductDetailSection",
        cascade="all, delete-orphan",
        order_by="ProductDetailSection.position",
    )
    media_items = relationship(
        "ProductMediaItem",
        cascade="all, delete-orphan",
        order_by="ProductMediaItem.position",
    )
    order_items = relationship("OrderItem", back_populates="product")
    categories = relationship("Category", secondary=product_categories, order_by="Category.sort_order")

    @property
    def final_price(self) -> int:
        return apply_discount(self.price, self.discount_percent)


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    alt_text = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="images")
