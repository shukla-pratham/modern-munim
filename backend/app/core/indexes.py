"""
Database index definitions for performance optimization.
These indexes are created via Alembic migrations.
"""
# This file documents recommended indexes. Actual indexes are created via Alembic.

# Recommended indexes (add to migration):
# - products.stock_quantity (for filtering low stock)
# - orders.created_at (for time-based queries)
# - order_items.product_id (for product sales queries)
# - expenses.product_id (for product expense queries)
# - stock_transactions.product_id, created_at (for transaction history)
# - demand_forecasts.product_id, forecast_date, created_at (for AI queries)
# - stockout_predictions.product_id, created_at (for AI queries)
# - restocking_recommendations.product_id, created_at (for AI queries)
# - dead_stock_detections.product_id, created_at (for AI queries)
# - ai_alerts.product_id, created_at, is_read (for alert queries)
# - job_runs.job_type, status, started_at (for job monitoring)

# Most indexes are already created via model definitions (index=True on columns)
# Additional composite indexes can be added in migrations if needed for specific query patterns
