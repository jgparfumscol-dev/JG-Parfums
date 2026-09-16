from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from database import Base


class ContactMessage(Base):
    """Mensaje dejado desde /contacto.html. Sin cuenta de usuario asociada
    (cualquier visitante puede escribir) — el admin lo revisa y responde
    por su cuenta (WhatsApp, correo, teléfono), acá solo queda el registro."""

    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=False)  # correo o teléfono, lo que el visitante prefiera dejar
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
