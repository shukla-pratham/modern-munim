from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_workspace, WorkspaceContext
from app.schemas.inventory import (
    StockInRequest, StockOutRequest, StockTransactionResponse, ThresholdUpdate
)
from app.schemas.product import ProductResponse
from app.services.inventory_service import (
    stock_in, stock_out, get_stock_transactions, update_stock_threshold
)

router = APIRouter()


@router.post("/stock-in", response_model=StockTransactionResponse)
def add_stock(
    request: StockInRequest,
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Add stock to a product scoped to workspace."""
    transaction = stock_in(
        db,
        product_id=request.product_id,
        quantity=request.quantity,
        workspace_id=workspace.workspace_id,
        reason=request.reason,
        is_demo=workspace.is_demo,
    )
    
    return StockTransactionResponse(
        id=transaction.id,
        product_id=transaction.product_id,
        product_name=transaction.product.name,
        quantity_change=transaction.quantity_change,
        transaction_type=transaction.transaction_type.value,
        reason=transaction.reason,
        created_at=transaction.created_at
    )


@router.post("/stock-out", response_model=StockTransactionResponse)
def remove_stock(
    request: StockOutRequest,
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Remove stock from a product scoped to workspace."""
    transaction = stock_out(
        db,
        product_id=request.product_id,
        quantity=request.quantity,
        workspace_id=workspace.workspace_id,
        reason=request.reason,
        is_demo=workspace.is_demo,
    )
    
    return StockTransactionResponse(
        id=transaction.id,
        product_id=transaction.product_id,
        product_name=transaction.product.name,
        quantity_change=transaction.quantity_change,
        transaction_type=transaction.transaction_type.value,
        reason=transaction.reason,
        created_at=transaction.created_at
    )


@router.get("/transactions", response_model=List[StockTransactionResponse])
def list_transactions(
    product_id: int = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Get stock transactions scoped to workspace."""
    transactions = get_stock_transactions(
        db,
        workspace_id=workspace.workspace_id,
        product_id=product_id,
        skip=skip,
        limit=limit,
    )
    
    return [
        StockTransactionResponse(
            id=t.id,
            product_id=t.product_id,
            product_name=t.product.name,
            quantity_change=t.quantity_change,
            transaction_type=t.transaction_type.value,
            reason=t.reason,
            created_at=t.created_at
        )
        for t in transactions
    ]


@router.put("/products/{product_id}/threshold", response_model=ProductResponse)
def update_product_threshold(
    product_id: int,
    threshold_data: ThresholdUpdate,
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Update stock threshold for a product scoped to workspace."""
    return update_stock_threshold(
        db,
        product_id=product_id,
        threshold=threshold_data.stock_threshold,
        workspace_id=workspace.workspace_id,
    )

