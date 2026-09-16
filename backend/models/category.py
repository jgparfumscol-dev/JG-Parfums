from sqlalchemy import Boolean, Column, Integer, String

from database import Base


class Category(Base):
    """Categoría de catálogo (antes 'familia olfativa' de texto libre).

    Administrable desde el panel: crear una acá es lo único que hace que un
    valor nuevo aparezca en el filtro del catálogo — antes el filtro tenía
    una lista fija en el código que no tenía por qué coincidir con lo que el
    admin escribía libremente en la ficha de producto.

    De cara al admin, en la pestaña del panel esto se llama "Clases" (y
    alimenta el carrusel de clases del home) — el nombre interno se queda
    igual para no tocar la tabla, la ruta ni el resto de consumidores
    (filtro del catálogo, ficha de producto, sección "Productos").
    """

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    # Foto + texto de la tarjeta del carrusel de clases — mismo vocabulario
    # que banner/galería (ver PageSection), pero como columnas propias
    # porque acá no hay un `content` JSON, es una fila de verdad.
    image_url = Column(String, nullable=True)
    eyebrow = Column(String, nullable=True)
    display_name = Column(String, nullable=True)  # si es null, la tarjeta usa `name`
    overlay_darkness = Column(Integer, nullable=False, default=40)  # 0-100
    text_position = Column(String, nullable=False, default="left")  # left | center | right
    blur = Column(Integer, nullable=False, default=0)  # 0-20px, mismo rango que banner/galería
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
