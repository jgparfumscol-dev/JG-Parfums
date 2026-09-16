from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database import Base


class Brand(Base):
    """Marca (logo) mostrada en el carrusel de marcas del home. Sin relación
    con `Product.house` (texto libre) — el catálogo no filtra por marca hoy,
    así que acá `link_url` es un enlace libre que pone el admin, no un
    filtro automático.
    """

    __tablename__ = "brands"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    logo_url = Column(String, nullable=False)
    link_url = Column(String, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
