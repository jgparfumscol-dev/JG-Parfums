"""add contact_messages and seed envios/politicas/contacto pages

Revision ID: b2d3e4f5a6b7
Revises: a1c2d3e4f5a6
Create Date: 2026-09-16 10:00:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2d3e4f5a6b7'
down_revision: Union[str, None] = 'a1c2d3e4f5a6'
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

# Contenido inicial de las páginas nuevas — texto editable desde el panel
# (secciones de tipo "text", igual que cualquier otra sección freeform), no
# hardcodeado en el HTML. El admin lo ajusta después sin pedirlo acá.
_SEED_SECTIONS = [
    {
        'page': 'envios', 'position': 0,
        'content': {
            'heading': 'Envíos',
            'body': 'Todos los envíos son gratuitos: el costo queda cubierto con la compra de tu perfume, no se cobra nada aparte al pagar.',
        },
    },
    {
        'page': 'envios', 'position': 1,
        'content': {
            'heading': 'Tiempos de entrega',
            'body': 'Cali: 1 a 2 días hábiles.\nResto del país: 3 a 5 días hábiles.',
        },
    },
    {
        'page': 'politicas', 'position': 0,
        'content': {
            'heading': 'Cambios y devoluciones',
            'body': 'Si el perfume que recibiste no cumple tus expectativas, tienes 5 días calendario desde la entrega para avisarnos y solicitar un cambio.',
        },
    },
    {
        'page': 'politicas', 'position': 1,
        'content': {
            'heading': 'Productos dañados o defectuosos',
            'body': 'Si tu pedido llega dañado o con un defecto, contáctanos dentro de las 48 horas siguientes a la entrega para coordinar el reemplazo sin costo adicional.',
        },
    },
    {
        'page': 'politicas', 'position': 2,
        'content': {
            'heading': 'Condiciones para el cambio',
            'body': 'El producto debe conservar su empaque original, etiquetas y todas sus partes, sin señales de uso, golpes ni manchas.\nLos decants (5ml y 10ml) no admiten cambio ni devolución, por tratarse de productos fraccionados de uso personal.',
        },
    },
    {
        'page': 'politicas', 'position': 3,
        'content': {
            'heading': 'Cómo solicitar un cambio',
            'body': 'Escríbenos por WhatsApp o al correo de contacto con tus datos, la fecha de compra y fotos del producto.\nUna vez aprobado el cambio, debes enviarlo de vuelta en las condiciones originales.',
        },
    },
    {
        'page': 'politicas', 'position': 4,
        'content': {
            'heading': 'Gastos de envío en cambios',
            'body': 'El costo de envío para devolver el producto corre por cuenta del cliente, salvo que el cambio se deba a un error nuestro o a un defecto de fábrica.',
        },
    },
    {
        'page': 'politicas', 'position': 5,
        'content': {
            'heading': 'Garantía y reembolsos',
            'body': 'Si el defecto se repite después del reemplazo, procede la devolución del dinero conforme a la Ley 1480 de protección al consumidor.\nLos reembolsos aprobados se procesan entre 24 y 48 horas.',
        },
    },
    {
        'page': 'contacto', 'position': 0,
        'content': {
            'heading': 'Contacto',
            'body': '¿Tienes una pregunta sobre un pedido o un perfume? Escríbenos y te respondemos lo antes posible.',
        },
    },
]


def upgrade() -> None:
    op.create_table(
        'contact_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_contact_messages_created_at'), 'contact_messages', ['created_at'], unique=False)

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
        _page_sections_table.delete().where(
            _page_sections_table.c.page.in_(['envios', 'politicas', 'contacto'])
        )
    )
    op.drop_index(op.f('ix_contact_messages_created_at'), table_name='contact_messages')
    op.drop_table('contact_messages')
