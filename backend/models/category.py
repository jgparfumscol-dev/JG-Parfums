from sqlalchemy import Column, Integer, String

from database import Base


class Category(Base):
    """Categoría de catálogo (antes 'familia olfativa' de texto libre).

    Administrable desde el panel: crear una acá es lo único que hace que un
    valor nuevo aparezca en el filtro del catálogo — antes el filtro tenía
    una lista fija en el código que no tenía por qué coincidir con lo que el
    admin escribía libremente en la ficha de producto.
    """

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
