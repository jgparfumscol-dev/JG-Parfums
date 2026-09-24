"""products many-to-many categories

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Un producto pasa de tener una sola clase (products.category_id) a
    # poder estar en una, dos o más — tabla puente sin columnas propias,
    # mismo criterio que cualquier N:N simple.
    op.create_table(
        'product_categories',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('product_id', 'category_id'),
    )

    # Backfill: cada producto que ya tenía una categoría asignada queda con
    # esa misma como su única fila en la tabla puente.
    bind = op.get_bind()
    products_table = sa.table(
        'products', sa.column('id', sa.Integer), sa.column('category_id', sa.Integer)
    )
    product_categories_table = sa.table(
        'product_categories', sa.column('product_id', sa.Integer), sa.column('category_id', sa.Integer)
    )
    rows = bind.execute(
        sa.select(products_table.c.id, products_table.c.category_id)
        .where(products_table.c.category_id.isnot(None))
    ).all()
    if rows:
        bind.execute(
            product_categories_table.insert(),
            [{'product_id': product_id, 'category_id': category_id} for product_id, category_id in rows],
        )

    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_constraint('fk_products_category_id_categories', type_='foreignkey')
        batch_op.drop_column('category_id')


def downgrade() -> None:
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_products_category_id_categories', 'categories', ['category_id'], ['id'], ondelete='SET NULL'
        )

    # Un producto en varias clases no vuelve a entrar en una sola columna:
    # se queda con la de menor id como su "categoría principal" — es una
    # pérdida de información aceptada al bajar de versión.
    bind = op.get_bind()
    products_table = sa.table(
        'products', sa.column('id', sa.Integer), sa.column('category_id', sa.Integer)
    )
    product_categories_table = sa.table(
        'product_categories', sa.column('product_id', sa.Integer), sa.column('category_id', sa.Integer)
    )
    rows = bind.execute(
        sa.select(
            product_categories_table.c.product_id,
            sa.func.min(product_categories_table.c.category_id),
        ).group_by(product_categories_table.c.product_id)
    ).all()
    for product_id, category_id in rows:
        bind.execute(
            products_table.update()
            .where(products_table.c.id == product_id)
            .values(category_id=category_id)
        )

    op.drop_table('product_categories')
