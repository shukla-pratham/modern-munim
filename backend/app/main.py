from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.api import (
    auth, products, orders, inventory, expenses, dashboard,
    ai_insights, vendors, purchase_orders, workspaces
)
from app.core.middleware import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.core.startup_validation import validate_startup_config
from app.core.logging_config import configure_logging
import logging
import os

configure_logging()
logger = logging.getLogger(__name__)

if os.getenv("ENVIRONMENT") == "production":
    validate_startup_config()

app = FastAPI(
    title="Marketplace API",
    description="Inventory, Expense, and Marketplace Platform - Phase 1 & 2 (AI/ML)",
    version="2.0.0"
)

allowed_hosts = settings.get_allowed_hosts_list()
if allowed_hosts and "*" not in allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

cors_origins = settings.get_cors_origins_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(workspaces.router, prefix="/api/workspaces", tags=["workspaces"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["expenses"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(ai_insights.router, prefix="/api/ai", tags=["ai-insights"])
app.include_router(vendors.router, prefix="/api/vendors", tags=["vendors"])
app.include_router(purchase_orders.router, prefix="/api/purchase-orders", tags=["purchase-orders"])


@app.get("/")
def root():
    return {"message": "Marketplace API - Phase 1 & 2 (AI/ML)", "version": "2.0.0"}


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns basic system status.
    """
    from app.core.database import engine
    from sqlalchemy import text
    
    try:
        # Check database connectivity
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        logger.exception("Database health check failed")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "2.0.0"
    }
