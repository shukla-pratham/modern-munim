from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    stock_quantity: int = 0
    stock_threshold: int = 10


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock_threshold: Optional[int] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    stock_quantity: int
    stock_threshold: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
