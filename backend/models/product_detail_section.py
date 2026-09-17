from sqlalchemy import Column, ForeignKey, Integer, String, Text

from database import Base


class ProductDetailSection(Base):
    """Bloque desplegable propio de la ficha (ej. "Modo de uso", "Ingredientes").

    Contenido libre pensado en Markdown/plano simple, no HTML: se muestra
    dentro de un <details> en la ficha del producto. `position` ordena la
    lista, igual que ProductNote.
    """

    __tablename__ = "product_detail_sections"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    position = Column(Integer, nullable=False, default=0)
