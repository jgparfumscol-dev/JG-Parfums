from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String

from database import Base


class PageSection(Base):
    """Bloque de contenido administrable de una página del sitio (banner, testimonios,
    contadores o HTML/CSS libre). `content` cambia de forma según `type`; se valida
    a nivel de ruta, no acá — es contenido de un único admin de confianza.
    """

    __tablename__ = "page_sections"

    id = Column(Integer, primary_key=True)
    page = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    content = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
