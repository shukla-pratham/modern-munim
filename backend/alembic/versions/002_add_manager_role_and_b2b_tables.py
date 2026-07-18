"""Add manager role and B2B tables

Revision ID: 002_b2b_tables
Revises: 001_initial
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_b2b_tables'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'manager' to userrole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'manager'")
    
    # Create suppliers table
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('contact_phone', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('payment_terms', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('lead_time_days >= 0', name='check_lead_time_non_negative')
    )
    op.create_index(op.f('ix_suppliers_id'), 'suppliers', ['id'], unique=False)
    op.create_index(op.f('ix_suppliers_name'), 'suppliers', ['name'], unique=False)
    
    # Create purchase_orders table
    op.create_table(
        'purchase_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('po_number', sa.String(), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('order_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expected_delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.CheckConstraint('total_amount >= 0', name='check_po_amount_non_negative')
    )
    op.create_index(op.f('ix_purchase_orders_id'), 'purchase_orders', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_supplier_id'), 'purchase_orders', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_po_number'), 'purchase_orders', ['po_number'], unique=True)
    
    # Create purchase_order_items table
    op.create_table(
        'purchase_order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.CheckConstraint('quantity > 0', name='check_po_item_quantity_positive'),
        sa.CheckConstraint('unit_cost >= 0', name='check_po_item_cost_non_negative'),
        sa.CheckConstraint('total_cost >= 0', name='check_po_item_total_non_negative')
    )
    op.create_index(op.f('ix_purchase_order_items_id'), 'purchase_order_items', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_order_items_purchase_order_id'), 'purchase_order_items', ['purchase_order_id'], unique=False)
    op.create_index(op.f('ix_purchase_order_items_product_id'), 'purchase_order_items', ['product_id'], unique=False)
    
    # Create inventory_snapshots table
    op.create_table(
        'inventory_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('quantity_on_hand', sa.Integer(), nullable=False),
        sa.Column('quantity_reserved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_available', sa.Integer(), nullable=False),
        sa.Column('unit_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('total_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('days_supply', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.CheckConstraint('quantity_on_hand >= 0', name='check_snapshot_on_hand_non_negative'),
        sa.CheckConstraint('quantity_reserved >= 0', name='check_snapshot_reserved_non_negative'),
        sa.CheckConstraint('quantity_available >= 0', name='check_snapshot_available_non_negative'),
        sa.CheckConstraint('unit_cost >= 0', name='check_snapshot_unit_cost_non_negative'),
        sa.CheckConstraint('total_value >= 0', name='check_snapshot_total_value_non_negative')
    )
    op.create_index(op.f('ix_inventory_snapshots_id'), 'inventory_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_snapshots_product_id'), 'inventory_snapshots', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_snapshots_snapshot_date'), 'inventory_snapshots', ['snapshot_date'], unique=False)
    op.create_index('ix_inventory_snapshots_product_date', 'inventory_snapshots', ['product_id', 'snapshot_date'], unique=False)


def downgrade() -> None:
    op.drop_table('inventory_snapshots')
    op.drop_table('purchase_order_items')
    op.drop_table('purchase_orders')
    op.drop_table('suppliers')
    # Note: Cannot remove enum value in PostgreSQL, so we leave 'manager' in userrole enum
