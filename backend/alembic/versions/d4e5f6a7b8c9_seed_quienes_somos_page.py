"""seed quienes-somos page

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-18 09:00:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_page_sections_table = sa.table(
    'page_sections',
    sa.column('id', sa.Integer),
    sa.column('page', sa.String),
    sa.column('type', sa.String),
    sa.column('position', sa.Integer),
    sa.column('is_active', sa.Boolean),
    sa.column('content', sa.JSON),
    sa.column('key', sa.String),
    sa.column('is_builtin', sa.Boolean),
    sa.column('created_at', sa.DateTime),
)

# Texto inicial de /quienes-somos.html — editable desde el panel (secciones
# de tipo "text", igual que envíos/políticas/contacto).
_SEED_SECTIONS = [
    {
        'page': 'quienes-somos', 'position': 0,
        'content': {
            'heading': 'Quiénes somos',
            'body': 'JG Parfums es una tienda de perfumes originales de nicho, con sede en Cali, Colombia. Nace de una necesidad clara: llevarle a las personas fragancias de calidad, cien por ciento originales, al mejor precio posible.',
        },
    },
    {
        'page': 'quienes-somos', 'position': 1,
        'content': {
            'heading': 'Lo que nos distingue',
            'body': 'En JG Parfums solo se comercializa perfumería original — de nicho y de casas reconocidas —, sin réplicas ni imitaciones. Cada frasco es el original de la marca que lo produce.',
        },
    },
    {
        'page': 'quienes-somos', 'position': 2,
        'content': {
            'heading': 'Decants',
            'body': 'Los decants son el mismo perfume original, fraccionado en un frasco pequeño para que cada cliente pueda probarlo antes de decidirse por el frasco completo.',
        },
    },
    {
        'page': 'quienes-somos', 'position': 3,
        'content': {
            'heading': 'Nuestra historia',
            'body': 'JG Parfums fue fundada en 2018 por Jhon Gutiérrez, con el propósito de acercar la perfumería de nicho y las fragancias originales a más personas en Colombia.',
        },
    },
]


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(timezone.utc)
    connection.execute(
        _page_sections_table.insert(),
        [
            {
                'page': s['page'], 'type': 'text', 'position': s['position'],
                'is_active': True, 'content': s['content'], 'key': None, 'is_builtin': False,
                'created_at': now,
            }
            for s in _SEED_SECTIONS
        ],
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        _page_sections_table.delete().where(_page_sections_table.c.page == 'quienes-somos')
    )
