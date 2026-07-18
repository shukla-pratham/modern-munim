"""Create purchase_orders and purchase_order_items if missing

When 002 was stamped but not run, vendors exist (from 003) but purchase_orders
does not. This migration creates those tables in the current schema so the app works.

Revision ID: 004_po_if_missing
Revises: 003_vendor_intelligence
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa

revision = "004_po_if_missing"
down_revision = "003_vendor_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    has_po = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'purchase_orders'")
    ).scalar()
    if has_po:
        return

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("po_number", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="created"),
        sa.Column("total_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("order_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("promised_delivery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_delivery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delay_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.CheckConstraint("total_cost >= 0", name="check_po_cost_non_negative"),
    )
    op.create_index("ix_purchase_orders_id", "purchase_orders", ["id"], unique=False)
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"], unique=True)
    op.create_index("ix_purchase_orders_vendor_id", "purchase_orders", ["vendor_id"], unique=False)
    op.create_index("ix_purchase_orders_vendor_status", "purchase_orders", ["vendor_id", "status"], unique=False)
    op.create_index("ix_purchase_orders_delivery_dates", "purchase_orders", ["promised_delivery_date", "actual_delivery_date"], unique=False)

    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.CheckConstraint("quantity > 0", name="check_po_item_quantity_positive"),
        sa.CheckConstraint("unit_cost >= 0", name="check_po_item_cost_non_negative"),
        sa.CheckConstraint("total_cost >= 0", name="check_po_item_total_non_negative"),
    )
    op.create_index("ix_purchase_order_items_id", "purchase_order_items", ["id"], unique=False)
    op.create_index("ix_purchase_order_items_purchase_order_id", "purchase_order_items", ["purchase_order_id"], unique=False)
    op.create_index("ix_purchase_order_items_product_id", "purchase_order_items", ["product_id"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    has_po = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'purchase_orders'")
    ).scalar()
    if not has_po:
        return
    op.drop_index("ix_purchase_order_items_product_id", table_name="purchase_order_items")
    op.drop_index("ix_purchase_order_items_purchase_order_id", table_name="purchase_order_items")
    op.drop_index("ix_purchase_order_items_id", table_name="purchase_order_items")
    op.drop_table("purchase_order_items")
    op.drop_index("ix_purchase_orders_delivery_dates", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_vendor_status", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_vendor_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_po_number", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_id", table_name="purchase_orders")
    op.drop_table("purchase_orders")
