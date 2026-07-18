"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (idempotent for partial runs)
    for name, values in [
        ("userrole", "('customer', 'admin')"),
        ("orderstatus", "('pending', 'completed', 'cancelled')"),
        ("expensecategory", "('inventory', 'operations', 'marketing')"),
        ("expensetype", "('one_time', 'recurring')"),
        ("transactiontype", "('in', 'out')"),
        ("trendtype", "('rising', 'stable', 'declining')"),
        ("jobstatus", "('running', 'completed', 'failed', 'cancelled')"),
    ]:
        op.execute(
            f"DO $$ BEGIN CREATE TYPE {name} AS ENUM {values}; EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
        )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', postgresql.ENUM('customer', 'admin', name='userrole', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('stock_threshold', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('stock_quantity >= 0', name='check_stock_quantity_non_negative'),
        sa.CheckConstraint('stock_threshold >= 0', name='check_stock_threshold_non_negative'),
        sa.CheckConstraint('price >= 0', name='check_price_non_negative')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'completed', 'cancelled', name='orderstatus', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    
    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price_at_purchase', sa.Numeric(10, 2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index(op.f('ix_order_items_id'), 'order_items', ['id'], unique=False)
    
    # Create expenses table
    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', postgresql.ENUM('inventory', 'operations', 'marketing', name='expensecategory', create_type=False), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('expense_type', postgresql.ENUM('one_time', 'recurring', name='expensetype', create_type=False), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index(op.f('ix_expenses_id'), 'expenses', ['id'], unique=False)
    
    # Create stock_transactions table
    op.create_table(
        'stock_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity_change', sa.Integer(), nullable=False),
        sa.Column('transaction_type', postgresql.ENUM('in', 'out', name='transactiontype', create_type=False), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index(op.f('ix_stock_transactions_id'), 'stock_transactions', ['id'], unique=False)
    
    # Create AI forecast tables
    op.create_table(
        'demand_forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('forecast_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('forecasted_quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('trend', postgresql.ENUM('rising', 'stable', 'declining', name='trendtype', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index(op.f('ix_demand_forecasts_id'), 'demand_forecasts', ['id'], unique=False)
    op.create_index(op.f('ix_demand_forecasts_product_id'), 'demand_forecasts', ['product_id'], unique=False)
    op.create_index(op.f('ix_demand_forecasts_forecast_date'), 'demand_forecasts', ['forecast_date'], unique=False)
    op.create_index(op.f('ix_demand_forecasts_created_at'), 'demand_forecasts', ['created_at'], unique=False)
    
    op.create_table(
        'stockout_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('days_until_stockout', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('sales_velocity', sa.Numeric(10, 2), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index(op.f('ix_stockout_predictions_id'), 'stockout_predictions', ['id'], unique=False)
    op.create_index(op.f('ix_stockout_predictions_product_id'), 'stockout_predictions', ['product_id'], unique=False)
    op.create_index(op.f('ix_stockout_predictions_created_at'), 'stockout_predictions', ['created_at'], unique=False)
    
    op.create_table(
        'restocking_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('recommended_quantity', sa.Integer(), nullable=False),
        sa.Column('recommended_timing_days', sa.Integer(), nullable=False),
        sa.Column('should_restock', sa.String(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('demand_forecast_impact', sa.Numeric(5, 2), nullable=True),
        sa.Column('margin_impact', sa.Numeric(5, 2), nullable=True),
        sa.Column('stock_risk_impact', sa.Numeric(5, 2), nullable=True),
        sa.Column('cost_impact', sa.Numeric(5, 2), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index(op.f('ix_restocking_recommendations_id'), 'restocking_recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_restocking_recommendations_product_id'), 'restocking_recommendations', ['product_id'], unique=False)
    op.create_index(op.f('ix_restocking_recommendations_created_at'), 'restocking_recommendations', ['created_at'], unique=False)
    
    op.create_table(
        'dead_stock_detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('is_dead_stock', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('demand_trend', sa.String(), nullable=True),
        sa.Column('days_since_last_sale', sa.Integer(), nullable=True),
        sa.Column('holding_cost_ratio', sa.Numeric(5, 2), nullable=True),
        sa.Column('margin_status', sa.String(), nullable=True),
        sa.Column('suggested_action', sa.String(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index(op.f('ix_dead_stock_detections_id'), 'dead_stock_detections', ['id'], unique=False)
    op.create_index(op.f('ix_dead_stock_detections_product_id'), 'dead_stock_detections', ['product_id'], unique=False)
    op.create_index(op.f('ix_dead_stock_detections_created_at'), 'dead_stock_detections', ['created_at'], unique=False)
    
    op.create_table(
        'ai_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index(op.f('ix_ai_alerts_id'), 'ai_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_ai_alerts_product_id'), 'ai_alerts', ['product_id'], unique=False)
    op.create_index(op.f('ix_ai_alerts_created_at'), 'ai_alerts', ['created_at'], unique=False)
    
    # Create job_runs table
    op.create_table(
        'job_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False, server_default='ai_batch_processing'),
        sa.Column('status', postgresql.ENUM('running', 'completed', 'failed', 'cancelled', name='jobstatus', create_type=False), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('products_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('forecasts_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('predictions_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('recommendations_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('detections_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('alerts_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('lock_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_runs_id'), 'job_runs', ['id'], unique=False)
    op.create_index(op.f('ix_job_runs_job_type'), 'job_runs', ['job_type'], unique=False)
    op.create_index(op.f('ix_job_runs_status'), 'job_runs', ['status'], unique=False)
    op.create_index(op.f('ix_job_runs_started_at'), 'job_runs', ['started_at'], unique=False)
    op.create_index(op.f('ix_job_runs_lock_id'), 'job_runs', ['lock_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('job_runs')
    op.drop_table('ai_alerts')
    op.drop_table('dead_stock_detections')
    op.drop_table('restocking_recommendations')
    op.drop_table('stockout_predictions')
    op.drop_table('demand_forecasts')
    op.drop_table('stock_transactions')
    op.drop_table('expenses')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS trendtype")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS expensetype")
    op.execute("DROP TYPE IF EXISTS expensecategory")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
