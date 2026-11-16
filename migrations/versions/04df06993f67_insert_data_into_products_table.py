"""Insert data into products table

Revision ID: 04df06993f67
Revises: b6726028a649
Create Date: 2026-11-17 00:52:56.223608

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04df06993f67'
down_revision = 'b6726028a649'
branch_labels = None
depends_on = None


from sqlalchemy.sql import table, column

def upgrade():
    categories_table = table('categories', column('id', sa.Integer), column('name', sa.String))
    op.bulk_insert(categories_table, [
        {'name': 'Electronics'}, {'name': 'Books'}, {'name': 'Clothing'},
    ])

    conn = op.get_bind()
    def cid(name):
        return conn.execute(
            sa.text("SELECT id FROM categories WHERE name = :n"), {"n": name}
        ).scalar()

    products_table = table('products',
        column('name', sa.String), column('price', sa.Float),
        column('active', sa.Boolean), column('category_id', sa.Integer))
    op.bulk_insert(products_table, [
        {'name': 'Laptop',     'price': 1200.0, 'active': True,  'category_id': cid('Electronics')},
        {'name': 'Smartphone', 'price': 800.0,  'active': True,  'category_id': cid('Electronics')},
        {'name': 'Novel',      'price': 20.0,   'active': True,  'category_id': cid('Books')},
        {'name': 'T-Shirt',    'price': 25.0,   'active': False, 'category_id': cid('Clothing')},
    ])

def downgrade():
    op.execute("DELETE FROM products WHERE name IN ('Laptop','Smartphone','Novel','T-Shirt')")
    op.execute("DELETE FROM categories WHERE name IN ('Electronics','Books','Clothing')")
