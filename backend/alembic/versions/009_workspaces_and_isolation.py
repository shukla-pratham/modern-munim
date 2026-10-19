"""Add workspace multi-tenant models and scoped business columns

Revision ID: 009_add_workspaces_and_tenant_isolation
Revises: 008_user_store_type
Create Date: 2026-10-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

revision = "009_workspaces_isolation"
down_revision = "008_user_store_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0. Ensure enum types have lowercase values matching application models and initial schema
    with op.get_context().autocommit_block():
        for val in ("in", "out"):
            op.execute(f"ALTER TYPE transactiontype ADD VALUE IF NOT EXISTS '{val}'")
        for val in ("inventory", "operations", "marketing", "salary", "miscellaneous"):
            op.execute(f"ALTER TYPE expensecategory ADD VALUE IF NOT EXISTS '{val}'")
        for val in ("one_time", "recurring"):
            op.execute(f"ALTER TYPE expensetype ADD VALUE IF NOT EXISTS '{val}'")
        for val in ("pending", "completed", "cancelled"):
            op.execute(f"ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS '{val}'")
        for val in ("rising", "stable", "declining"):
            op.execute(f"ALTER TYPE trendtype ADD VALUE IF NOT EXISTS '{val}'")
        for val in ("running", "completed", "failed", "cancelled"):
            op.execute(f"ALTER TYPE jobstatus ADD VALUE IF NOT EXISTS '{val}'")

    # Migrate any legacy uppercase values safely
    op.execute("UPDATE stock_transactions SET transaction_type = 'in' WHERE transaction_type::text = 'STOCK_IN'")
    op.execute("UPDATE stock_transactions SET transaction_type = 'out' WHERE transaction_type::text = 'STOCK_OUT'")
    op.execute("UPDATE expenses SET category = 'inventory' WHERE category::text = 'INVENTORY'")
    op.execute("UPDATE expenses SET category = 'operations' WHERE category::text = 'OPERATIONS'")
    op.execute("UPDATE expenses SET category = 'marketing' WHERE category::text = 'MARKETING'")
    op.execute("UPDATE expenses SET expense_type = 'one_time' WHERE expense_type::text = 'ONE_TIME'")
    op.execute("UPDATE expenses SET expense_type = 'recurring' WHERE expense_type::text = 'RECURRING'")
    op.execute("UPDATE orders SET status = 'pending' WHERE status::text = 'PENDING'")
    op.execute("UPDATE orders SET status = 'completed' WHERE status::text = 'COMPLETED'")
    op.execute("UPDATE orders SET status = 'cancelled' WHERE status::text = 'CANCELLED'")
    op.execute("UPDATE demand_forecasts SET trend = 'rising' WHERE trend::text = 'RISING'")
    op.execute("UPDATE demand_forecasts SET trend = 'stable' WHERE trend::text = 'STABLE'")
    op.execute("UPDATE demand_forecasts SET trend = 'declining' WHERE trend::text = 'DECLINING'")
    op.execute("UPDATE job_runs SET status = 'running' WHERE status::text = 'RUNNING'")
    op.execute("UPDATE job_runs SET status = 'completed' WHERE status::text = 'COMPLETED'")
    op.execute("UPDATE job_runs SET status = 'failed' WHERE status::text = 'FAILED'")
    op.execute("UPDATE job_runs SET status = 'cancelled' WHERE status::text = 'CANCELLED'")

    # 1. Create workspaces table
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("store_type", sa.String(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("onboarding_step", sa.String(), nullable=False, server_default="store_profile"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )

    # 2. Create workspace_memberships table
    op.create_table(
        "workspace_memberships",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(), nullable=False, server_default="owner"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user_membership"),
    )

    # 3. Add workspace_id (nullable) to business tables and tag is_demo on business rows
    business_tables = [
        "products",
        "vendors",
        "expenses",
        "purchase_orders",
        "stock_transactions",
        "orders",
        "inventory_snapshots",
        "demand_forecasts",
        "stockout_predictions",
        "restocking_recommendations",
        "dead_stock_detections",
        "ai_alerts",
    ]

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    for table in business_tables:
        if table in existing_tables:
            op.add_column(table, sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True))
            op.add_column(table, sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="false"))

    # Align ai_alerts schema with AIAlert model (title and is_read columns)
    if "ai_alerts" in existing_tables:
        ai_alert_columns = {col["name"] for col in inspector.get_columns("ai_alerts")}
        if "title" not in ai_alert_columns:
            op.add_column("ai_alerts", sa.Column("title", sa.String(), nullable=False, server_default="AI Alert"))
        if "is_read" not in ai_alert_columns:
            op.add_column("ai_alerts", sa.Column("is_read", sa.String(), nullable=False, server_default="no"))
        if "product_id" in ai_alert_columns:
            op.alter_column("ai_alerts", "product_id", nullable=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    business_tables = [
        "ai_alerts",
        "dead_stock_detections",
        "restocking_recommendations",
        "stockout_predictions",
        "demand_forecasts",
        "inventory_snapshots",
        "orders",
        "stock_transactions",
        "purchase_orders",
        "expenses",
        "vendors",
        "products",
    ]
    for table in business_tables:
        if table in existing_tables:
            op.drop_column(table, "is_demo")
            op.drop_column(table, "workspace_id")

    op.drop_table("workspace_memberships")
    op.drop_table("workspaces")
