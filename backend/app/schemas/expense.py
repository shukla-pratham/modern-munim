from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ExpenseCreate(BaseModel):
    category: str  # inventory, operations, marketing
    description: str
    amount: Decimal
    expense_type: str = "one_time"  # one_time, recurring
    product_id: Optional[int] = None


class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    expense_type: Optional[str] = None
    product_id: Optional[int] = None


class ExpenseResponse(BaseModel):
    id: int
    category: str
    description: str
    amount: Decimal
    expense_type: str
    product_id: Optional[int]
    product_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
