"""add categories, replace product olfactory_family

Revision ID: 839ff7a8a1cf
Revises: ddc7d92b42df
Create Date: 2026-09-11 11:01:45.823329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '839ff7a8a1cf'
down_revision: Union[str, None] = 'ddc7d92b42df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=True)

    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_products_category_id_categories', 'categories', ['category_id'], ['id'], ondelete='SET NULL'
        )

    # Backfill: cada valor distinto de la antigua "familia olfativa" de texto
    # libre se convierte en una categoría real administrable, y los productos
    # que la usaban quedan enlazados a ella.
    bind = op.get_bind()
    categories_table = sa.table(
        'categories', sa.column('id', sa.Integer), sa.column('name', sa.String), sa.column('slug', sa.String)
    )
    products_table = sa.table(
        'products', sa.column('id', sa.Integer), sa.column('olfactory_family', sa.String), sa.column('category_id', sa.Integer)
    )

    distinct_families = [
        row[0] for row in bind.execute(
            sa.select(products_table.c.olfactory_family)
            .where(products_table.c.olfactory_family.isnot(None))
            .distinct()
        )
        if row[0] and row[0].strip()
    ]

    for family in distinct_families:
        family = family.strip()
        result = bind.execute(
            categories_table.insert()
            .values(name=family.capitalize(), slug=family.lower())
            .returning(categories_table.c.id)
        )
        category_id = result.scalar_one()
        bind.execute(
            products_table.update()
            .where(products_table.c.olfactory_family == family)
            .values(category_id=category_id)
        )

    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_column('olfactory_family')


def downgrade() -> None:
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('olfactory_family', sa.String(), nullable=True))

    bind = op.get_bind()
    categories_table = sa.table(
        'categories', sa.column('id', sa.Integer), sa.column('name', sa.String), sa.column('slug', sa.String)
    )
    products_table = sa.table(
        'products', sa.column('id', sa.Integer), sa.column('olfactory_family', sa.String), sa.column('category_id', sa.Integer)
    )
    for category_id, name in bind.execute(sa.select(categories_table.c.id, categories_table.c.name)):
        bind.execute(
            products_table.update()
            .where(products_table.c.category_id == category_id)
            .values(olfactory_family=name)
        )

    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_constraint('fk_products_category_id_categories', type_='foreignkey')
        batch_op.drop_column('category_id')

    op.drop_index(op.f('ix_categories_slug'), table_name='categories')
    op.drop_table('categories')
