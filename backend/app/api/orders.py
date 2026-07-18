from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, OrderItemResponse
from app.services.order_service import create_order, get_user_orders, get_order, get_all_orders

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=201)
def create_new_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new order (checkout) - customer only"""
    order = create_order(db, current_user.id, order_data)
    
    # Convert to response format with product names
    items_response = []
    for item in order.items:
        items_response.append(OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name,
            quantity=item.quantity,
            price_at_purchase=item.price_at_purchase
        ))
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status.value,
        created_at=order.created_at,
        items=items_response
    )


@router.get("", response_model=List[OrderResponse])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all orders (admin only)"""
    orders = get_all_orders(db, skip=skip, limit=limit)
    
    result = []
    for order in orders:
        items_response = [
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                price_at_purchase=item.price_at_purchase
            )
            for item in order.items
        ]
        result.append(OrderResponse(
            id=order.id,
            user_id=order.user_id,
            total_amount=order.total_amount,
            status=order.status.value,
            created_at=order.created_at,
            items=items_response
        ))
    
    return result


@router.get("/my-orders", response_model=List[OrderResponse])
def list_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's orders"""
    orders = get_user_orders(db, current_user.id, skip=skip, limit=limit)
    
    result = []
    for order in orders:
        items_response = [
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                price_at_purchase=item.price_at_purchase
            )
            for item in order.items
        ]
        result.append(OrderResponse(
            id=order.id,
            user_id=order.user_id,
            total_amount=order.total_amount,
            status=order.status.value,
            created_at=order.created_at,
            items=items_response
        ))
    
    return result


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single order by ID (user can only see their own orders unless admin)"""
    # Admin can see any order, users can only see their own
    if current_user.role == "admin":
        order = get_order(db, order_id)
    else:
        order = get_order(db, order_id, user_id=current_user.id)
    
    items_response = [
        OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name,
            quantity=item.quantity,
            price_at_purchase=item.price_at_purchase
        )
        for item in order.items
    ]
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status.value,
        created_at=order.created_at,
        items=items_response
    )
