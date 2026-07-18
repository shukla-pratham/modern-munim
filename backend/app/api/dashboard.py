from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.schemas.dashboard import (
    RevenueResponse, ExpenseBreakdownResponse, ProfitResponse,
    StockStatusResponse, SalesResponse
)
from app.services.dashboard_service import (
    get_revenue_data, get_expense_breakdown, get_profit_data,
    get_stock_status, get_sales_data
)

router = APIRouter()


@router.get("/revenue", response_model=RevenueResponse)
def get_revenue(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get revenue data for dashboard (admin only)"""
    data = get_revenue_data(db, days=days)
    return RevenueResponse(**data)


@router.get("/expenses", response_model=ExpenseBreakdownResponse)
def get_expenses_breakdown(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get expense breakdown for dashboard (admin only)"""
    data = get_expense_breakdown(db, days=days)
    return ExpenseBreakdownResponse(**data)


@router.get("/profit", response_model=ProfitResponse)
def get_profit(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get profit data for dashboard (admin only)"""
    data = get_profit_data(db, days=days)
    return ProfitResponse(**data)


@router.get("/stock-status", response_model=StockStatusResponse)
def get_stock_status_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get stock status for dashboard (admin only)"""
    data = get_stock_status(db)
    return StockStatusResponse(**data)


@router.get("/sales", response_model=SalesResponse)
def get_sales(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get sales data for dashboard (admin only)"""
    data = get_sales_data(db, days=days)
    return SalesResponse(**data)
