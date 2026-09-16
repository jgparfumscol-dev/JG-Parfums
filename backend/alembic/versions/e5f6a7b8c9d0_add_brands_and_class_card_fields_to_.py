"""add brands table and class-card fields to categories

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-16 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default en las NOT NULL: categories ya puede tener filas reales
    # y todas deben seguir siendo válidas sin que el admin tenga que tocarlas.
    with op.batch_alter_table('categories') as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('eyebrow', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('display_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('overlay_darkness', sa.Integer(), nullable=False, server_default='40'))
        batch_op.add_column(sa.Column('text_position', sa.String(), nullable=False, server_default='left'))
        batch_op.add_column(sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))

    op.create_table(
        'brands',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('logo_url', sa.String(), nullable=False),
        sa.Column('link_url', sa.String(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('brands')

    with op.batch_alter_table('categories') as batch_op:
        batch_op.drop_column('is_active')
        batch_op.drop_column('sort_order')
        batch_op.drop_column('text_position')
        batch_op.drop_column('overlay_darkness')
        batch_op.drop_column('display_name')
        batch_op.drop_column('eyebrow')
        batch_op.drop_column('image_url')
