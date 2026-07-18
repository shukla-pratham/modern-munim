from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status
from decimal import Decimal
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.product_service import get_product
from app.core.transaction import db_transaction, lock_product_for_update
from app.core.exceptions import InsufficientStockError, ValidationError
import logging

logger = logging.getLogger(__name__)


def create_order(db: Session, user_id: int, order_data: OrderCreate) -> Order:
    """
    Create a new order with order items.
    Uses database transactions and row-level locking to prevent race conditions.
    """
    # Validate input
    if not order_data.items or len(order_data.items) == 0:
        raise ValidationError("Order must contain at least one item")
    
    # Use transaction to ensure atomicity
    with db_transaction(db):
        total_amount = Decimal("0.00")
        order_items = []
        locked_products = {}  # Cache locked products to avoid re-locking
        
        # First pass: validate all items and lock products
        for item_data in order_data.items:
            # Validate quantity
            if item_data.quantity <= 0:
                raise ValidationError(f"Quantity must be positive for product {item_data.product_id}")
            
            # Lock product for update (prevents race conditions)
            product = lock_product_for_update(db, item_data.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {item_data.product_id} not found"
                )
            
            # Check stock availability (using locked product)
            if product.stock_quantity < item_data.quantity:
                raise InsufficientStockError(
                    product_name=product.name,
                    available=product.stock_quantity,
                    requested=item_data.quantity
                )
            
            locked_products[product.id] = product
        
        # Second pass: create order items and update stock
        for item_data in order_data.items:
            product = locked_products[item_data.product_id]
            
            # Calculate item total
            item_total = product.price * item_data.quantity
            total_amount += item_total
            
            # Create order item
            order_item = OrderItem(
                product_id=product.id,
                quantity=item_data.quantity,
                price_at_purchase=product.price
            )
            order_items.append(order_item)
            
            # Update product stock (already locked, so safe)
            product.stock_quantity -= item_data.quantity
            if product.stock_quantity < 0:
                # Double-check: this should never happen due to validation above
                raise InsufficientStockError(
                    product_name=product.name,
                    available=product.stock_quantity + item_data.quantity,
                    requested=item_data.quantity
                )
        
        # Create order
        db_order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status=OrderStatus.COMPLETED,  # Simulated checkout - auto-complete
            items=order_items
        )
        db.add(db_order)
        # Transaction commits automatically via context manager
    
    db.refresh(db_order)
    logger.info(f"Order {db_order.id} created for user {user_id} with {len(order_items)} items")
    return db_order


def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    """Get all orders for a user"""
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_order(db: Session, order_id: int, user_id: int = None) -> Order:
    """Get a single order by ID (optionally filtered by user)"""
    query = db.query(Order).filter(Order.id == order_id)
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    order = query.first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


def get_all_orders(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    """Get all orders (admin only)"""
    return db.query(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
