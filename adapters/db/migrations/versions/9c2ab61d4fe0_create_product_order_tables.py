"""create product and order tables

Revision ID: 9c2ab61d4fe0
Revises: 563415b7668a
Create Date: 2026-09-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c2ab61d4fe0"
down_revision: Union[str, Sequence[str], None] = "563415b7668a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


order_status_enum = sa.Enum(
    "PENDING",
    "PAID",
    "PROCESSING",
    "SHIPPED",
    "DELIVERED",
    "CANCELED",
    "RETURNED",
    name="orderstatusenum",
)


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("product_id"),
    )
    op.create_index("ix_products_product_id", "products", ["product_id"])

    op.create_table(
        "orders",
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", order_status_enum, nullable=False),
        sa.PrimaryKeyConstraint("order_id"),
    )
    op.create_index("ix_orders_order_id", "orders", ["order_id"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])

    op.create_table(
        "order_items",
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.order_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"]),
        sa.PrimaryKeyConstraint("item_id"),
    )
    op.create_index("ix_order_items_item_id", "order_items", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_order_items_item_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_index("ix_orders_order_id", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_products_product_id", table_name="products")
    op.drop_table("products")
    order_status_enum.drop(op.get_bind(), checkfirst=True)