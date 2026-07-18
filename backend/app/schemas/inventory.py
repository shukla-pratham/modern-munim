from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StockInRequest(BaseModel):
    product_id: int
    quantity: int
    reason: Optional[str] = "Manual restock"


class StockOutRequest(BaseModel):
    product_id: int
    quantity: int
    reason: Optional[str] = "Sale"


class ThresholdUpdate(BaseModel):
    stock_threshold: int


class StockTransactionResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity_change: int
    transaction_type: str
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
