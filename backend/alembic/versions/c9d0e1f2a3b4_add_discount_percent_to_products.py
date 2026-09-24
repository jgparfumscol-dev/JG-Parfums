"""add discount_percent to products

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-09-24 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default='0': products ya tiene filas reales en producción y la
    # columna es NOT NULL — 0 = sin descuento.
    op.add_column('products', sa.Column('discount_percent', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('products', 'discount_percent')
