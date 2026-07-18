from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal


class RevenueResponse(BaseModel):
    total_revenue: Decimal
    period: str  # e.g., "last_30_days", "all_time"
    daily_revenue: List[dict]  # [{date, revenue}, ...]


class ExpenseBreakdownResponse(BaseModel):
    total_expenses: Decimal
    by_category: dict  # {category: amount}
    by_type: dict  # {one_time: amount, recurring: amount}
    monthly_expenses: List[dict]  # [{month, amount}, ...]


class ProfitResponse(BaseModel):
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    profit_margin: Decimal  # percentage
    profit_by_product: List[dict]  # [{product_id, product_name, revenue, expenses, profit, margin}, ...]


class StockStatusResponse(BaseModel):
    total_products: int
    low_stock_products: List[dict]  # [{product_id, name, stock_quantity, threshold}, ...]
    out_of_stock_products: List[dict]
    stock_value: Decimal  # Total value of inventory


class SalesResponse(BaseModel):
    total_sales: int  # Total number of orders
    total_revenue: Decimal
    sales_by_product: List[dict]  # [{product_id, name, quantity_sold, revenue}, ...]
    sales_over_time: List[dict]  # [{date, orders, revenue}, ...]
