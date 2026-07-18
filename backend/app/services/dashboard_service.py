from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.expense import Expense, ExpenseCategory, ExpenseType


def get_revenue_data(db: Session, days: int = 30) -> Dict:
    """Calculate revenue data for dashboard"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total revenue
    total_revenue_query = db.query(func.sum(Order.total_amount)).filter(
        Order.status == "completed",
        Order.created_at >= cutoff_date
    )
    total_revenue = total_revenue_query.scalar() or Decimal("0.00")
    
    # Daily revenue breakdown
    daily_revenue = db.query(
        func.date(Order.created_at).label("date"),
        func.sum(Order.total_amount).label("revenue")
    ).filter(
        Order.status == "completed",
        Order.created_at >= cutoff_date
    ).group_by(func.date(Order.created_at)).all()
    
    daily_revenue_list = [
        {"date": str(row.date), "revenue": float(row.revenue)}
        for row in daily_revenue
    ]
    
    return {
        "total_revenue": total_revenue,
        "period": f"last_{days}_days",
        "daily_revenue": daily_revenue_list
    }


def get_expense_breakdown(db: Session, days: int = 30) -> Dict:
    """Calculate expense breakdown for dashboard"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    expenses = db.query(Expense).filter(Expense.created_at >= cutoff_date).all()
    
    total_expenses = sum(exp.amount for exp in expenses)
    
    # By category
    by_category = {}
    for category in ExpenseCategory:
        category_total = sum(
            exp.amount for exp in expenses if exp.category == category
        )
        by_category[category.value] = float(category_total)
    
    # By type
    by_type = {}
    for exp_type in ExpenseType:
        type_total = sum(
            exp.amount for exp in expenses if exp.expense_type == exp_type
        )
        by_type[exp_type.value] = float(type_total)
    
    # Monthly expenses
    monthly_expenses = db.query(
        extract("year", Expense.created_at).label("year"),
        extract("month", Expense.created_at).label("month"),
        func.sum(Expense.amount).label("amount")
    ).filter(
        Expense.created_at >= cutoff_date
    ).group_by(
        extract("year", Expense.created_at),
        extract("month", Expense.created_at)
    ).all()
    
    monthly_list = [
        {"month": f"{int(row.year)}-{int(row.month):02d}", "amount": float(row.amount)}
        for row in monthly_expenses
    ]
    
    return {
        "total_expenses": Decimal(str(total_expenses)),
        "by_category": by_category,
        "by_type": by_type,
        "monthly_expenses": monthly_list
    }


def get_profit_data(db: Session, days: int = 30) -> Dict:
    """Calculate profit data for dashboard"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total revenue
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status == "completed",
        Order.created_at >= cutoff_date
    ).scalar() or Decimal("0.00")
    
    # Total expenses
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.created_at >= cutoff_date
    ).scalar() or Decimal("0.00")
    
    # Net profit
    net_profit = total_revenue - total_expenses
    
    # Profit margin (percentage)
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0.00")
    
    # Profit by product
    product_revenue = db.query(
        OrderItem.product_id,
        Product.name,
        func.sum(OrderItem.quantity * OrderItem.price_at_purchase).label("revenue"),
        func.sum(OrderItem.quantity).label("quantity_sold")
    ).join(
        Order, OrderItem.order_id == Order.id
    ).join(
        Product, OrderItem.product_id == Product.id
    ).filter(
        Order.status == "completed",
        Order.created_at >= cutoff_date
    ).group_by(
        OrderItem.product_id, Product.name
    ).all()
    
    profit_by_product = []
    for row in product_revenue:
        # Get expenses for this product
        product_expenses = db.query(func.sum(Expense.amount)).filter(
            Expense.product_id == row.product_id,
            Expense.created_at >= cutoff_date
        ).scalar() or Decimal("0.00")
        
        product_revenue_amount = row.revenue or Decimal("0.00")
        product_profit = product_revenue_amount - product_expenses
        product_margin = (product_profit / product_revenue_amount * 100) if product_revenue_amount > 0 else Decimal("0.00")
        
        profit_by_product.append({
            "product_id": row.product_id,
            "product_name": row.name,
            "revenue": float(product_revenue_amount),
            "expenses": float(product_expenses),
            "profit": float(product_profit),
            "margin": float(product_margin)
        })
    
    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": profit_margin,
        "profit_by_product": profit_by_product
    }


def get_stock_status(db: Session) -> Dict:
    """Get stock status for dashboard"""
    products = db.query(Product).all()
    
    total_products = len(products)
    low_stock_products = []
    out_of_stock_products = []
    stock_value = Decimal("0.00")
    
    for product in products:
        # Calculate stock value
        stock_value += product.price * product.stock_quantity
        
        # Check stock status
        if product.stock_quantity == 0:
            out_of_stock_products.append({
                "product_id": product.id,
                "name": product.name,
                "stock_quantity": product.stock_quantity,
                "threshold": product.stock_threshold
            })
        elif product.stock_quantity <= product.stock_threshold:
            low_stock_products.append({
                "product_id": product.id,
                "name": product.name,
                "stock_quantity": product.stock_quantity,
                "threshold": product.stock_threshold
            })
    
    return {
        "total_products": total_products,
        "low_stock_products": low_stock_products,
        "out_of_stock_products": out_of_stock_products,
        "stock_value": stock_value
    }


def get_sales_data(db: Session, days: int = 30) -> Dict:
    """Get sales data for dashboard"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total sales (number of orders)
    total_sales = db.query(func.count(Order.id)).filter(
        Order.status == "completed",
        Order.created_at >= cutoff_date
    ).scalar() or 0
    
    # Total revenue
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status == "completed",
        Order.created_at >= cutoff_date
    ).scalar() or Decimal("0.00")
    
    # Sales by product
    sales_by_product = db.query(
        OrderItem.product_id,
        Product.name,
        func.sum(OrderItem.quantity).label("quantity_sold"),
        func.sum(OrderItem.quantity * OrderItem.price_at_purchase).label("revenue")
    ).join(
        Order, OrderItem.order_id == Order.id
    ).join(
        Product, OrderItem.product_id == Product.id
    ).filter(
        Order.status == "completed",
        Order.created_at >= cutoff_date
    ).group_by(
        OrderItem.product_id, Product.name
    ).all()
    
    sales_by_product_list = [
        {
            "product_id": row.product_id,
            "name": row.name,
            "quantity_sold": int(row.quantity_sold or 0),
            "revenue": float(row.revenue or 0)
        }
        for row in sales_by_product
    ]
    
    # Sales over time
    sales_over_time = db.query(
        func.date(Order.created_at).label("date"),
        func.count(Order.id).label("orders"),
        func.sum(Order.total_amount).label("revenue")
    ).filter(
        Order.status == "completed",
        Order.created_at >= cutoff_date
    ).group_by(
        func.date(Order.created_at)
    ).all()
    
    sales_over_time_list = [
        {
            "date": str(row.date),
            "orders": int(row.orders),
            "revenue": float(row.revenue or 0)
        }
        for row in sales_over_time
    ]
    
    return {
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "sales_by_product": sales_by_product_list,
        "sales_over_time": sales_over_time_list
    }
