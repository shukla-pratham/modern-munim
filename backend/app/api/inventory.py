from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
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
    current_user: User = Depends(get_current_admin)
):
    """Add stock to a product (admin only)"""
    transaction = stock_in(db, request.product_id, request.quantity, request.reason)
    
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
    current_user: User = Depends(get_current_admin)
):
    """Remove stock from a product (admin only)"""
    transaction = stock_out(db, request.product_id, request.quantity, request.reason)
    
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
    current_user: User = Depends(get_current_admin)
):
    """Get stock transactions (admin only)"""
    transactions = get_stock_transactions(db, product_id=product_id, skip=skip, limit=limit)
    
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
    current_user: User = Depends(get_current_admin)
):
    """Update stock threshold for a product (admin only)"""
    return update_stock_threshold(db, product_id, threshold_data.stock_threshold)
