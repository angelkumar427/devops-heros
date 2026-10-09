"""create products table

Revision ID: 0001
Revises:
Create Date: 2026-10-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sku", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer, nullable=False, server_default="10"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity >= 0", name="ck_products_quantity_non_negative"),
        sa.CheckConstraint("unit_price >= 0", name="ck_products_price_non_negative"),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_category", "products", ["category"])


def downgrade() -> None:
    op.drop_index("ix_products_category", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
