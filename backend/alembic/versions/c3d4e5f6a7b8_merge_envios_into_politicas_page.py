"""merge envios page sections into politicas

Revision ID: c3d4e5f6a7b8
Revises: b2d3e4f5a6b7
Create Date: 2026-09-17 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_page_sections_table = sa.table(
    'page_sections',
    sa.column('id', sa.Integer),
    sa.column('page', sa.String),
    sa.column('position', sa.Integer),
)


def upgrade() -> None:
    # /envios.html se elimina y su contenido pasa a vivir arriba del todo en
    # /politicas.html (ahora "Envíos y políticas"). Se reordena por posición
    # actual en vez de asumir el contenido original de la seed, porque el
    # admin ya pudo haber editado estas secciones desde el panel en
    # producción — el merge tiene que respetar lo que haya ahora, no lo que
    # se sembró originalmente.
    connection = op.get_bind()

    envios_ids = [
        row[0]
        for row in connection.execute(
            sa.select(_page_sections_table.c.id)
            .where(_page_sections_table.c.page == 'envios')
            .order_by(_page_sections_table.c.position)
        )
    ]
    politicas_ids = [
        row[0]
        for row in connection.execute(
            sa.select(_page_sections_table.c.id)
            .where(_page_sections_table.c.page == 'politicas')
            .order_by(_page_sections_table.c.position)
        )
    ]

    next_position = 0
    for section_id in envios_ids:
        connection.execute(
            _page_sections_table.update()
            .where(_page_sections_table.c.id == section_id)
            .values(page='politicas', position=next_position)
        )
        next_position += 1
    for section_id in politicas_ids:
        connection.execute(
            _page_sections_table.update()
            .where(_page_sections_table.c.id == section_id)
            .values(position=next_position)
        )
        next_position += 1


def downgrade() -> None:
    # No reversible con precisión: una vez fusionadas, las secciones que
    # venían de "envios" ya no se pueden distinguir de las que ya estaban en
    # "politicas" (mucho menos si el admin las editó después del merge). Se
    # deja como no-op — bajar esta revisión no separa el contenido de nuevo.
    pass
