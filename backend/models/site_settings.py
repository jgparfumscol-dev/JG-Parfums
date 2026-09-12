from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class SiteSettings(Base):
    """Configuración global de la tienda — fila única (id=1). Nombre, color de
    marca, tipografía y datos de contacto que el sitio público lee en cada
    carga de página; el checkout lee el costo de envío desde acá también.
    """

    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True)
    store_name = Column(String, nullable=False, default="JG Parfums")
    accent_color = Column(String, nullable=False, default="#D3AE6A")
    font_pairing = Column(String, nullable=False, default="classic")
    whatsapp_number = Column(String, nullable=True)
    instagram_url = Column(String, nullable=True)
    tiktok_url = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    shipping_cost = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
