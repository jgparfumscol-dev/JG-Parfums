from sqlalchemy import Column, ForeignKey, Integer, String

from database import Base


class ProductNote(Base):
    """Nota olfativa individual de un producto: nombre y color libres,
    elegidos por el admin. `position` ordena la escalera — 0 es la más
    suave (arriba), la posición más alta es la más fuerte (abajo).
    """

    __tablename__ = "product_notes"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)
