from sqlalchemy import Column, ForeignKey, Integer, String

from database import Base


class ProductMediaItem(Base):
    """Bloque de medio (foto, GIF o video corto) debajo de la descripción de
    la ficha. Cada uno es una franja propia con texto superpuesto opcional,
    igual criterio que la galería de secciones de página (ver
    renderGalleryImageMedia en sections.js): posición del texto, oscurecido
    y desenfoque configurables por bloque. `height_px` y `width_pct`
    controlan la finura (alto) y el ancho que ocupa en pantalla — a
    diferencia de la galería de secciones, aquí cada bloque se apila a todo
    lo alto en vez de vivir en un grid/carrusel.
    """

    __tablename__ = "product_media_items"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    alt_text = Column(String, nullable=False, default="")
    title = Column(String, nullable=True)
    subtitle = Column(String, nullable=True)
    text_position = Column(String, nullable=False, default="left")  # left | center | right
    text_position_vertical = Column(String, nullable=False, default="bottom")  # top | center | bottom
    overlay_opacity = Column(Integer, nullable=False, default=0)  # 0-100, oscurecido
    blur = Column(Integer, nullable=False, default=0)  # 0-20, desenfoque en px
    height_px = Column(Integer, nullable=False, default=480)  # finura/alto del bloque
    width_pct = Column(Integer, nullable=False, default=100)  # ancho ocupado en pantalla
    position = Column(Integer, nullable=False, default=0)
