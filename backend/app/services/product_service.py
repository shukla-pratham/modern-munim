from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False
) -> List[Product]:
    """Get products with optional filtering"""
    query = db.query(Product)
    
    # Search filter
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    
    # Price filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Stock filter
    if in_stock_only:
        query = query.filter(Product.stock_quantity > 0)
    
    return query.offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int) -> Product:
    """Get a single product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


def create_product(db: Session, product_data: ProductCreate) -> Product:
    """Create a new product"""
    db_product = Product(**product_data.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product_data: ProductUpdate) -> Product:
    """Update an existing product"""
    product = get_product(db, product_id)
    
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    """Delete a product"""
    product = get_product(db, product_id)
    db.delete(product)
    db.commit()
