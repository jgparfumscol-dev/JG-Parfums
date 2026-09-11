from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class PageView(Base):
    """Una visita a una página del sitio (no del panel admin). Sin cookies,
    sin IP ni user-agent guardados — solo qué página y cuándo, lo mínimo
    para saber si el sitio tiene tráfico y qué se mira más."""

    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False, index=True)
    referrer = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
