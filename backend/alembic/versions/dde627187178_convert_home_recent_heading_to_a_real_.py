"""convert home_recent_heading to a real products section

Revision ID: dde627187178
Revises: edf994ac09bc
Create Date: 2026-09-16 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dde627187178'
down_revision: Union[str, None] = 'edf994ac09bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_page_sections_table = sa.table(
    'page_sections',
    sa.column('type', sa.String),
    sa.column('content', sa.JSON),
    sa.column('key', sa.String),
)

_OLD_CONTENT = {'heading': 'Recién llegados'}
_NEW_CONTENT = {'heading': 'Recién llegados', 'category_id': None, 'limit': 8}


def upgrade() -> None:
    # "home_recent_heading" era solo un título (section_heading) pegado a
    # una grilla de productos hardcodeada en index.html: no se podía editar
    # qué productos mostraba ni moverla junto al resto de secciones. Pasa a
    # ser una sección "products" real (el tipo que ya existe para grillas
    # de producto en cualquier página) — mismo título, misma cantidad de
    # productos (8), sin filtro de categoría. Solo toca la fila si sigue
    # con el content original: si el admin ya la editó, se deja como está.
    connection = op.get_bind()
    connection.execute(
        _page_sections_table.update()
        .where(_page_sections_table.c.key == 'home_recent_heading')
        .where(_page_sections_table.c.type == 'section_heading')
        .values(type='products', content=_NEW_CONTENT)
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        _page_sections_table.update()
        .where(_page_sections_table.c.key == 'home_recent_heading')
        .where(_page_sections_table.c.type == 'products')
        .values(type='section_heading', content=_OLD_CONTENT)
    )
