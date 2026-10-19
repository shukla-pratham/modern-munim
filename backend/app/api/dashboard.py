from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_workspace, WorkspaceContext
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
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Get revenue data for dashboard scoped to workspace."""
    data = get_revenue_data(db, workspace_id=workspace.workspace_id, days=days)
    return RevenueResponse(**data)


@router.get("/expenses", response_model=ExpenseBreakdownResponse)
def get_expenses_breakdown(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Get expense breakdown for dashboard scoped to workspace."""
    data = get_expense_breakdown(db, workspace_id=workspace.workspace_id, days=days)
    return ExpenseBreakdownResponse(**data)


@router.get("/profit", response_model=ProfitResponse)
def get_profit(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Get profit data for dashboard scoped to workspace."""
    data = get_profit_data(db, workspace_id=workspace.workspace_id, days=days)
    return ProfitResponse(**data)


@router.get("/stock-status", response_model=StockStatusResponse)
def get_stock_status_dashboard(
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Get stock status for dashboard scoped to workspace."""
    data = get_stock_status(db, workspace_id=workspace.workspace_id)
    return StockStatusResponse(**data)


@router.get("/sales", response_model=SalesResponse)
def get_sales(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Get sales data for dashboard scoped to workspace."""
    data = get_sales_data(db, workspace_id=workspace.workspace_id, days=days)
    return SalesResponse(**data)

