from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status
from app.models.product import Product
from app.models.stock_transaction import StockTransaction, TransactionType
from app.services.product_service import get_product
from app.core.transaction import db_transaction, lock_product_for_update, safe_stock_update
from app.core.exceptions import InvalidStockOperationError, InsufficientStockError
import logging

logger = logging.getLogger(__name__)


def stock_in(db: Session, product_id: int, quantity: int, workspace_id: int, reason: str = "Manual restock", is_demo: bool = False) -> StockTransaction:
    """
    Add stock to a product scoped to workspace.
    Uses transaction and locking to ensure data integrity.
    """
    # Validate input
    if quantity <= 0:
        raise InvalidStockOperationError("Stock quantity must be positive")
    
    # Use transaction for atomicity
    with db_transaction(db):
        # Lock product for update
        product = lock_product_for_update(db, product_id)
        if not product or product.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        # Update product stock
        old_stock = product.stock_quantity
        product.stock_quantity += quantity
        
        # Validate: prevent overflow (sanity check)
        if product.stock_quantity < old_stock:  # Overflow check
            raise InvalidStockOperationError("Stock quantity overflow")
        
        # Create transaction record
        transaction = StockTransaction(
            product_id=product_id,
            quantity_change=quantity,
            transaction_type=TransactionType.STOCK_IN,
            reason=reason,
            workspace_id=workspace_id,
            is_demo=is_demo,
        )
        db.add(transaction)
        # Transaction commits automatically
    
    db.refresh(transaction)
    logger.info(f"Stock in: Product {product_id}, Quantity: {quantity}, New stock: {product.stock_quantity} in workspace {workspace_id}")
    return transaction


def stock_out(db: Session, product_id: int, quantity: int, workspace_id: int, reason: str = "Sale", is_demo: bool = False) -> StockTransaction:
    """
    Remove stock from a product scoped to workspace.
    Uses transaction and locking to prevent negative stock.
    """
    # Validate input
    if quantity <= 0:
        raise InvalidStockOperationError("Stock quantity must be positive")
    
    # Use transaction for atomicity
    with db_transaction(db):
        # Lock product for update
        product = lock_product_for_update(db, product_id)
        if not product or product.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        # Check stock availability (using locked product)
        if product.stock_quantity < quantity:
            raise InsufficientStockError(
                product_name=product.name,
                available=product.stock_quantity,
                requested=quantity
            )
        
        # Update product stock
        old_stock = product.stock_quantity
        product.stock_quantity -= quantity
        
        # Double-check: ensure we didn't go negative
        if product.stock_quantity < 0:
            raise InsufficientStockError(
                product_name=product.name,
                available=old_stock,
                requested=quantity
            )
        
        # Create transaction record
        transaction = StockTransaction(
            product_id=product_id,
            quantity_change=-quantity,
            transaction_type=TransactionType.STOCK_OUT,
            reason=reason,
            workspace_id=workspace_id,
            is_demo=is_demo,
        )
        db.add(transaction)
        # Transaction commits automatically
    
    db.refresh(transaction)
    logger.info(f"Stock out: Product {product_id}, Quantity: {quantity}, New stock: {product.stock_quantity} in workspace {workspace_id}")
    return transaction


def get_stock_transactions(db: Session, workspace_id: int, product_id: int = None, skip: int = 0, limit: int = 100) -> List[StockTransaction]:
    """Get stock transactions scoped to authorized workspace, optionally filtered by product"""
    query = db.query(StockTransaction).filter(StockTransaction.workspace_id == workspace_id)
    if product_id:
        query = query.filter(StockTransaction.product_id == product_id)
    
    return query.order_by(StockTransaction.created_at.desc()).offset(skip).limit(limit).all()


def update_stock_threshold(db: Session, product_id: int, threshold: int, workspace_id: int) -> Product:
    """Update stock threshold for a product scoped to workspace"""
    product = get_product(db, product_id, workspace_id=workspace_id)
    product.stock_threshold = threshold
    db.commit()
    db.refresh(product)
    return product

