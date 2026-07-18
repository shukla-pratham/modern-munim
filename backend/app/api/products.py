from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import (
    get_products, get_product, create_product, update_product, delete_product
)

router = APIRouter()


@router.get("", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get list of products with optional search and filters (public endpoint)"""
    products = get_products(
        db, skip=skip, limit=limit, search=search,
        min_price=min_price, max_price=max_price, in_stock_only=in_stock_only
    )
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID (public endpoint)"""
    return get_product(db, product_id)


@router.post("", response_model=ProductResponse, status_code=201)
def create_new_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new product (admin only)"""
    return create_product(db, product_data)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product_by_id(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a product (admin only)"""
    return update_product(db, product_id, product_data)


@router.delete("/{product_id}", status_code=204)
def delete_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a product (admin only)"""
    delete_product(db, product_id)
    return None
