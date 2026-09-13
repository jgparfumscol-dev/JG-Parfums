from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Product(Base):
    """Perfume original de nicho. Casi siempre una sola presentación (size_ml)."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    house = Column(String, nullable=True)  # casa/marca original del perfume
    description = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    concentration = Column(String, nullable=True)  # EDP, EDT, extrait de parfum
    size_ml = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)  # COP, pesos enteros (sin centavos)
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
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
    order_items = relationship("OrderItem", back_populates="product")
    category = relationship("Category")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    alt_text = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="images")
