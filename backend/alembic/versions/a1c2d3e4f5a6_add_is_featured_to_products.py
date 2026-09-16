"""add is_featured to products

Revision ID: a1c2d3e4f5a6
Revises: 05076c6a221e
Create Date: 2026-09-16 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c2d3e4f5a6'
down_revision: Union[str, None] = '05076c6a221e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default='0': products ya puede tener filas reales en producción
    # y la columna es NOT NULL.
    op.add_column('products', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('products', 'is_featured')
