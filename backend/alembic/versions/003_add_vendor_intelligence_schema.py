"""Add Vendor Intelligence schema

Revision ID: 003_vendor_intelligence
Revises: 002_b2b_tables
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_vendor_intelligence'
down_revision = '002_b2b_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create purchase_order_status enum (ignore if exists)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE purchaseorderstatus AS ENUM ('created', 'ordered', 'delivered', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    
    # Create vendors table
    op.create_table(
        'vendors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('avg_lead_time_days', sa.Integer(), nullable=True),
        sa.Column('reliability_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('cost_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('overall_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('avg_lead_time_days >= 0', name='check_vendor_lead_time_non_negative'),
        sa.CheckConstraint('reliability_score >= 0 AND reliability_score <= 100', name='check_reliability_score_range'),
        sa.CheckConstraint('cost_score >= 0 AND cost_score <= 100', name='check_cost_score_range'),
        sa.CheckConstraint('overall_score >= 0 AND overall_score <= 100', name='check_overall_score_range')
    )
    op.create_index(op.f('ix_vendors_id'), 'vendors', ['id'], unique=False)
    op.create_index(op.f('ix_vendors_name'), 'vendors', ['name'], unique=False)
    op.create_index(op.f('ix_vendors_is_active'), 'vendors', ['is_active'], unique=False)
    op.create_index('ix_vendors_overall_score', 'vendors', ['overall_score'], unique=False)
    op.create_index('ix_vendors_is_active_score', 'vendors', ['is_active', 'overall_score'], unique=False)
    op.execute("CREATE SEQUENCE IF NOT EXISTS vendors_id_seq; ALTER TABLE vendors ALTER COLUMN id SET DEFAULT nextval('vendors_id_seq');")
    
    # Create vendor_products table
    op.create_table(
        'vendor_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('unit_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('min_order_qty', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.CheckConstraint('unit_cost >= 0', name='check_vendor_product_cost_non_negative'),
        sa.CheckConstraint('min_order_qty > 0', name='check_vendor_product_min_qty_positive'),
        sa.CheckConstraint('lead_time_days >= 0', name='check_vendor_product_lead_time_non_negative')
    )
    op.create_index(op.f('ix_vendor_products_id'), 'vendor_products', ['id'], unique=False)
    op.create_index(op.f('ix_vendor_products_vendor_id'), 'vendor_products', ['vendor_id'], unique=False)
    op.create_index(op.f('ix_vendor_products_product_id'), 'vendor_products', ['product_id'], unique=False)
    op.create_index('ix_vendor_products_vendor_product', 'vendor_products', ['vendor_id', 'product_id'], unique=False)
    op.execute("CREATE SEQUENCE IF NOT EXISTS vendor_products_id_seq; ALTER TABLE vendor_products ALTER COLUMN id SET DEFAULT nextval('vendor_products_id_seq');")
    
    # Migrate suppliers to vendors if suppliers table exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'suppliers') THEN
                INSERT INTO vendors (name, is_active, avg_lead_time_days, created_at)
                SELECT name, true, lead_time_days, created_at
                FROM suppliers;
            END IF;
        END $$;
    """)
    
    # Only update purchase_orders if the table exists (002 was applied)
    conn = op.get_bind()
    has_po = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'purchase_orders'"
    )).scalar()
    if has_po:
        op.add_column('purchase_orders', sa.Column('vendor_id', sa.Integer(), nullable=True))
        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_orders' AND column_name = 'supplier_id') THEN
                    UPDATE purchase_orders po
                    SET vendor_id = (
                        SELECT v.id FROM vendors v
                        INNER JOIN suppliers s ON s.name = v.name
                        WHERE s.id = po.supplier_id
                        LIMIT 1
                    )
                    WHERE po.supplier_id IS NOT NULL;
                END IF;
            END $$;
        """)
        op.alter_column('purchase_orders', 'vendor_id', nullable=False)
        op.alter_column('purchase_orders', 'status', type_=sa.String(), server_default='created')
        op.add_column('purchase_orders', sa.Column('delay_days', sa.Integer(), nullable=True))
        op.alter_column('purchase_orders', 'expected_delivery_date', new_column_name='promised_delivery_date')
        op.alter_column('purchase_orders', 'received_date', new_column_name='actual_delivery_date')
        op.alter_column('purchase_orders', 'total_amount', new_column_name='total_cost')
        op.create_foreign_key('fk_purchase_orders_vendor', 'purchase_orders', 'vendors', ['vendor_id'], ['id'])
        op.create_index('ix_purchase_orders_vendor_status', 'purchase_orders', ['vendor_id', 'status'], unique=False)
        op.create_index('ix_purchase_orders_delivery_dates', 'purchase_orders', ['promised_delivery_date', 'actual_delivery_date'], unique=False)
        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_orders' AND column_name = 'supplier_id') THEN
                    ALTER TABLE purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_supplier_id_fkey;
                    ALTER TABLE purchase_orders DROP COLUMN supplier_id;
                END IF;
            END $$;
        """)
    
    # Create vendor_performance_metrics table
    op.create_table(
        'vendor_performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('metric_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('avg_lead_time', sa.Numeric(5, 2), nullable=True),
        sa.Column('on_time_delivery_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('fulfillment_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('avg_unit_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('price_variance', sa.Numeric(10, 2), nullable=True),
        sa.Column('delay_days_avg', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id']),
        sa.CheckConstraint('avg_lead_time >= 0', name='check_metric_lead_time_non_negative'),
        sa.CheckConstraint('on_time_delivery_rate >= 0 AND on_time_delivery_rate <= 100', name='check_otd_rate_range'),
        sa.CheckConstraint('fulfillment_rate >= 0 AND fulfillment_rate <= 100', name='check_fulfillment_rate_range'),
        sa.CheckConstraint('avg_unit_cost >= 0', name='check_metric_cost_non_negative'),
        sa.CheckConstraint('price_variance >= 0', name='check_price_variance_non_negative')
    )
    op.create_index(op.f('ix_vendor_performance_metrics_id'), 'vendor_performance_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_vendor_performance_metrics_vendor_id'), 'vendor_performance_metrics', ['vendor_id'], unique=False)
    op.create_index(op.f('ix_vendor_performance_metrics_metric_date'), 'vendor_performance_metrics', ['metric_date'], unique=False)
    op.create_index('ix_vendor_performance_vendor_date', 'vendor_performance_metrics', ['vendor_id', 'metric_date'], unique=False)
    op.execute("CREATE SEQUENCE IF NOT EXISTS vendor_performance_metrics_id_seq; ALTER TABLE vendor_performance_metrics ALTER COLUMN id SET DEFAULT nextval('vendor_performance_metrics_id_seq');")


def downgrade() -> None:
    op.drop_table('vendor_performance_metrics')
    conn = op.get_bind()
    has_po = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'purchase_orders'"
    )).scalar()
    if has_po:
        op.drop_index('ix_purchase_orders_delivery_dates', table_name='purchase_orders')
        op.drop_index('ix_purchase_orders_vendor_status', table_name='purchase_orders')
    op.drop_table('vendor_products')
    op.drop_table('vendors')
    op.execute("DROP TYPE IF EXISTS purchaseorderstatus")
