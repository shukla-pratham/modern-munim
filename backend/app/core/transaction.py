"""
Transaction management utilities.
Ensures atomic operations and prevents race conditions.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)


@contextmanager
def db_transaction(db: Session) -> Generator[Session, None, None]:
    """
    Context manager for database transactions.
    Automatically commits on success, rolls back on error.
    
    Usage:
        with db_transaction(db) as session:
            # Do database operations
            session.add(...)
            # Commit happens automatically on exit
    """
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction rolled back due to error: {e}")
        raise


def lock_product_for_update(db: Session, product_id: int):
    """
    Lock a product row for update to prevent race conditions.
    Use this before modifying stock quantities.
    
    Returns the locked product or None if not found.
    """
    from app.models.product import Product
    # Use SELECT FOR UPDATE to lock the row
    product = db.execute(
        select(Product).where(Product.id == product_id).with_for_update()
    ).scalar_one_or_none()
    return product


def lock_vendor_for_update(db: Session, vendor_id: int):
    """
    Lock a vendor row for update to prevent race conditions.
    Use this before updating vendor scores or metrics.
    
    Returns the locked vendor or None if not found.
    """
    from app.models.vendor import Vendor
    vendor = db.execute(
        select(Vendor).where(Vendor.id == vendor_id).with_for_update()
    ).scalar_one_or_none()
    return vendor


def safe_stock_update(
    db: Session,
    product_id: int,
    quantity_change: int,
    min_stock: int = 0
) -> bool:
    """
    Safely update stock with locking and validation.
    Prevents negative stock and race conditions.
    
    Args:
        db: Database session
        product_id: Product ID
        quantity_change: Positive for stock_in, negative for stock_out
        min_stock: Minimum allowed stock (default 0)
    
    Returns:
        True if update succeeded, False if it would result in negative stock
    
    Raises:
        ProductNotFoundError: If product doesn't exist
    """
    from app.models.product import Product
    from app.core.exceptions import ProductNotFoundError, InvalidStockOperationError
    
    # Lock product for update
    product = lock_product_for_update(db, product_id)
    if not product:
        raise ProductNotFoundError(product_id)
    
    # Calculate new stock
    new_stock = product.stock_quantity + quantity_change
    
    # Validate: cannot go below minimum
    if new_stock < min_stock:
        return False
    
    # Update stock
    product.stock_quantity = new_stock
    db.commit()
    return True
