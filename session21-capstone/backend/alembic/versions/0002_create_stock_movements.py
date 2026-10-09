"""create stock_movements table (audit trail of every stock change)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("change", sa.Integer, nullable=False),
        sa.Column("reason", sa.String(120), nullable=False),
        sa.Column("quantity_after", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])
    op.create_index("ix_stock_movements_created_at", "stock_movements", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_stock_movements_created_at", table_name="stock_movements")
    op.drop_index("ix_stock_movements_product_id", table_name="stock_movements")
    op.drop_table("stock_movements")
