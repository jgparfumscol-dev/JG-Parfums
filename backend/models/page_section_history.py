from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String

from database import Base


class PageSectionHistory(Base):
    """Snapshot de una `PageSection` en el momento de crearla, editarla,
    borrarla o restaurarla. No tiene FK real a `page_sections`: si la
    sección original se borra, su historial debe sobrevivir, así que cada
    fila guarda una copia completa y autocontenida del contenido en vez de
    depender de que la fila original siga existiendo.
    """

    __tablename__ = "page_section_history"

    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, nullable=True)  # referencia informativa; puede apuntar a una fila ya borrada
    page = Column(String, nullable=False, index=True)
    key = Column(String, nullable=True)
    type = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False)
    position = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # created | updated | deleted | restored
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
