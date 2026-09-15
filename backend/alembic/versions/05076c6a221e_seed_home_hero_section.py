"""seed home_hero section

Revision ID: 05076c6a221e
Revises: dde627187178
Create Date: 2026-09-16 14:20:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05076c6a221e'
down_revision: Union[str, None] = 'dde627187178'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_page_sections_table = sa.table(
    'page_sections',
    sa.column('page', sa.String),
    sa.column('type', sa.String),
    sa.column('position', sa.Integer),
    sa.column('is_active', sa.Boolean),
    sa.column('content', sa.JSON),
    sa.column('key', sa.String),
    sa.column('is_builtin', sa.Boolean),
    sa.column('created_at', sa.DateTime),
)

# Copy exacto del hero hardcodeado en index.html (ficha del perfume
# destacado, con la pirámide de notas) — el seed no cambia nada visible,
# solo lo hace editable/movible/ocultable como cualquier otra sección.
_CONTENT = {
    'eyebrow': 'Perfumería de nicho · Colombia',
    'heading': 'Un perfume se explica con hechos',
    'description': 'Toca cada fase de la pirámide para leer las notas reales — de salida, corazón y fondo — de este frasco.',
    'cta_label': 'Ver catálogo',
    'cta_link': '/catalogo.html',
    'diagram_heading': 'Así se lee un perfume en JG',
}


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(timezone.utc)
    connection.execute(
        _page_sections_table.insert(),
        [
            {
                'page': 'home', 'type': 'hero_product',
                # -1: siempre primero por defecto sin tener que renumerar las
                # secciones que ya existen (banner=0, productos=1, etc.) —
                # el admin la puede mover libremente después de todos modos.
                'position': -1,
                'is_active': True, 'content': _CONTENT, 'key': 'home_hero', 'is_builtin': True,
                'created_at': now,
            }
        ],
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        _page_sections_table.delete().where(_page_sections_table.c.key == 'home_hero')
    )
