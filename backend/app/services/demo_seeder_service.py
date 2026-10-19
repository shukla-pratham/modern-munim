"""
Founder-only, idempotent demo seed and reset service.
Guarded strictly to the verified founder email (shuklapratham758@gmail.com).
All seeded records are tagged with workspace_id and is_demo=True.
Reset removes strictly is_demo=True rows belonging to the founder's workspace.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.workspace import Workspace
from app.models.product import Product
from app.models.vendor import Vendor, VendorProduct, VendorPerformanceMetric
from app.models.expense import Expense, ExpenseCategory, ExpenseType
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus
from app.models.inventory_snapshot import InventorySnapshot
from app.models.stock_transaction import StockTransaction, TransactionType
from app.models.order import Order, OrderItem, OrderStatus
from app.models.ai_forecast import (
    DemandForecast, StockoutPrediction, RestockingRecommendation,
    DeadStockDetection, AIAlert, TrendType
)
from app.services.workspace_service import is_founder_user


def verify_founder_workspace_access(user: User, workspace: Workspace):
    """Ensure that the caller is the verified founder and operating in their demo workspace."""
    if not is_founder_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Demo seeding and reset are restricted to the verified SaaS founder."
        )


def seed_founder_demo_data(db: Session, user: User, workspace: Workspace) -> Dict[str, Any]:
    """
    Deterministically seeds demo catalog, vendors, purchase orders, expenses, and orders.
    Idempotent: If products with is_demo=True already exist for this workspace, no duplicates are added.
    """
    verify_founder_workspace_access(user, workspace)

    # 1. Check idempotency
    existing_count = db.query(Product).filter(
        Product.workspace_id == workspace.id,
        Product.is_demo == True
    ).count()

    if existing_count > 0:
        return {
            "status": "already_seeded",
            "message": "Demo data already exists in this workspace. No new records created.",
            "workspace_id": workspace.id,
            "products_count": existing_count
        }

    # 2. Seed Vendors
    vendors_data = [
        {"name": "TechSupply Direct", "avg_lead_time_days": 3, "reliability_score": Decimal("95.0"), "cost_score": Decimal("88.0"), "overall_score": Decimal("91.5")},
        {"name": "Global Office Essentials", "avg_lead_time_days": 5, "reliability_score": Decimal("90.0"), "cost_score": Decimal("92.0"), "overall_score": Decimal("91.0")},
        {"name": "Prime Components Ltd", "avg_lead_time_days": 7, "reliability_score": Decimal("85.0"), "cost_score": Decimal("96.0"), "overall_score": Decimal("90.5")},
    ]
    created_vendors = []
    for v in vendors_data:
        vendor = Vendor(
            name=v["name"],
            avg_lead_time_days=v["avg_lead_time_days"],
            reliability_score=v["reliability_score"],
            cost_score=v["cost_score"],
            overall_score=v["overall_score"],
            is_active=True,
            workspace_id=workspace.id,
            is_demo=True
        )
        db.add(vendor)
        created_vendors.append(vendor)
    db.flush()

    # 3. Seed Products
    products_data = [
        {"name": "Wireless Ergonomic Mouse", "description": "High precision wireless mouse", "price": Decimal("34.99"), "stock": 45, "threshold": 10},
        {"name": "Mechanical Gaming Keyboard", "description": "Tactile switch mechanical keyboard", "price": Decimal("119.99"), "stock": 25, "threshold": 8},
        {"name": "Thunderbolt Docking Station", "description": "Universal dual-display docking hub", "price": Decimal("189.99"), "stock": 15, "threshold": 5},
        {"name": "27-inch 4K Monitor", "description": "Ultra HD color calibrated IPS panel", "price": Decimal("349.99"), "stock": 10, "threshold": 4},
        {"name": "Noise Cancelling Headset", "description": "Over-ear active noise cancelling headset", "price": Decimal("149.99"), "stock": 30, "threshold": 6},
    ]
    created_products = []
    for p in products_data:
        prod = Product(
            name=p["name"],
            description=p["description"],
            price=p["price"],
            stock_quantity=p["stock"],
            stock_threshold=p["threshold"],
            workspace_id=workspace.id,
            is_demo=True
        )
        db.add(prod)
        created_products.append(prod)
    db.flush()

    # 4. Seed Stock Transaction ledger entries for initial stock
    for prod in created_products:
        tx = StockTransaction(
            product_id=prod.id,
            transaction_type=TransactionType.STOCK_IN,
            quantity_change=prod.stock_quantity,
            reason="Initial Founder Demo Inventory",
            workspace_id=workspace.id,
            is_demo=True
        )
        db.add(tx)
    db.flush()

    # 5. Seed Vendor Products
    for i, prod in enumerate(created_products):
        vendor = created_vendors[i % len(created_vendors)]
        vp = VendorProduct(
            vendor_id=vendor.id,
            product_id=prod.id,
            unit_cost=Decimal("18.00"),
            min_order_qty=5,
            lead_time_days=vendor.avg_lead_time_days
        )
        db.add(vp)
    db.flush()

    # 6. Seed Expenses
    expenses_data = [
        {"description": "Warehouse Operations - Oct 2026", "amount": Decimal("450.00"), "category": ExpenseCategory.OPERATIONS, "type": ExpenseType.RECURRING},
        {"description": "Logistics Freight Shipping", "amount": Decimal("1250.00"), "category": ExpenseCategory.OPERATIONS, "type": ExpenseType.ONE_TIME},
        {"description": "Digital Marketing Campaign", "amount": Decimal("320.00"), "category": ExpenseCategory.MARKETING, "type": ExpenseType.RECURRING},
        {"description": "Packaging Restock Supplies", "amount": Decimal("199.00"), "category": ExpenseCategory.INVENTORY, "type": ExpenseType.ONE_TIME},
    ]
    for exp in expenses_data:
        expense = Expense(
            description=exp["description"],
            amount=exp["amount"],
            category=exp["category"],
            expense_type=exp["type"],
            workspace_id=workspace.id,
            is_demo=True
        )
        db.add(expense)
    db.flush()

    # 7. Seed Purchase Order
    po = PurchaseOrder(
        vendor_id=created_vendors[0].id,
        po_number=f"PO-DEMO-{workspace.id}-001",
        status=PurchaseOrderStatus.DELIVERED.value,
        total_cost=Decimal("900.00"),
        workspace_id=workspace.id,
        is_demo=True
    )
    db.add(po)
    db.flush()

    po_item = PurchaseOrderItem(
        purchase_order_id=po.id,
        product_id=created_products[0].id,
        quantity=50,
        unit_cost=Decimal("18.00"),
        total_cost=Decimal("900.00")
    )
    db.add(po_item)
    db.flush()

    # 8. Seed Customer Order & Items
    order = Order(
        user_id=user.id,
        status=OrderStatus.COMPLETED,
        total_amount=Decimal("254.97"),
        workspace_id=workspace.id,
        is_demo=True
    )
    db.add(order)
    db.flush()

    order_items = [
        OrderItem(
            order_id=order.id,
            product_id=created_products[0].id,
            quantity=2,
            price_at_purchase=created_products[0].price
        ),
        OrderItem(
            order_id=order.id,
            product_id=created_products[1].id,
            quantity=1,
            price_at_purchase=created_products[1].price
        )
    ]
    for oi in order_items:
        db.add(oi)

    # 9. Seed AI Forecast & Alerts
    forecast = DemandForecast(
        product_id=created_products[0].id,
        forecast_date=datetime.utcnow() + timedelta(days=7),
        forecasted_quantity=Decimal("38.00"),
        confidence_score=Decimal("92.50"),
        trend=TrendType.RISING,
        workspace_id=workspace.id,
        is_demo=True
    )
    db.add(forecast)

    alert = AIAlert(
        alert_type="stockout",
        product_id=created_products[3].id,
        severity="medium",
        title="Restock Advisory: 4K Monitor",
        message="Stock is approaching safety threshold of 4 units based on sales velocity.",
        is_read="no",
        workspace_id=workspace.id,
        is_demo=True
    )
    db.add(alert)

    db.commit()

    return {
        "status": "success",
        "message": "Founder demo dataset seeded cleanly with workspace isolation.",
        "workspace_id": workspace.id,
        "vendors_created": len(created_vendors),
        "products_created": len(created_products),
        "orders_created": 1,
        "purchase_orders_created": 1
    }


def reset_founder_demo_data(db: Session, user: User, workspace: Workspace) -> Dict[str, Any]:
    """
    Safely and strictly purges ONLY rows where workspace_id == workspace.id AND is_demo == True.
    Never removes live production records or touches other workspaces.
    """
    verify_founder_workspace_access(user, workspace)

    # Get product IDs tagged is_demo in this workspace
    demo_product_ids = [
        p[0] for p in db.query(Product.id).filter(
            Product.workspace_id == workspace.id,
            Product.is_demo == True
        ).all()
    ]

    deleted_counts = {}

    # Clean dependent AI rows
    d1 = db.query(DemandForecast).filter(DemandForecast.workspace_id == workspace.id, DemandForecast.is_demo == True).delete()
    d2 = db.query(StockoutPrediction).filter(StockoutPrediction.workspace_id == workspace.id, StockoutPrediction.is_demo == True).delete()
    d3 = db.query(RestockingRecommendation).filter(RestockingRecommendation.workspace_id == workspace.id, RestockingRecommendation.is_demo == True).delete()
    d4 = db.query(DeadStockDetection).filter(DeadStockDetection.workspace_id == workspace.id, DeadStockDetection.is_demo == True).delete()
    d5 = db.query(AIAlert).filter(AIAlert.workspace_id == workspace.id, AIAlert.is_demo == True).delete()
    deleted_counts["ai_records"] = d1 + d2 + d3 + d4 + d5

    # Clean stock transactions
    deleted_counts["stock_transactions"] = db.query(StockTransaction).filter(
        StockTransaction.workspace_id == workspace.id,
        StockTransaction.is_demo == True
    ).delete()

    # Clean purchase orders & items
    demo_po_ids = [
        po[0] for po in db.query(PurchaseOrder.id).filter(
            PurchaseOrder.workspace_id == workspace.id,
            PurchaseOrder.is_demo == True
        ).all()
    ]
    if demo_po_ids:
        db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id.in_(demo_po_ids)).delete(synchronize_session=False)
    deleted_counts["purchase_orders"] = db.query(PurchaseOrder).filter(
        PurchaseOrder.workspace_id == workspace.id,
        PurchaseOrder.is_demo == True
    ).delete()

    # Clean orders & items
    demo_order_ids = [
        o[0] for o in db.query(Order.id).filter(
            Order.workspace_id == workspace.id,
            Order.is_demo == True
        ).all()
    ]
    if demo_order_ids:
        db.query(OrderItem).filter(OrderItem.order_id.in_(demo_order_ids)).delete(synchronize_session=False)
    deleted_counts["orders"] = db.query(Order).filter(
        Order.workspace_id == workspace.id,
        Order.is_demo == True
    ).delete()

    # Clean expenses
    deleted_counts["expenses"] = db.query(Expense).filter(
        Expense.workspace_id == workspace.id,
        Expense.is_demo == True
    ).delete()

    # Clean vendor products & metrics
    if demo_product_ids:
        db.query(VendorProduct).filter(VendorProduct.product_id.in_(demo_product_ids)).delete(synchronize_session=False)

    # Clean products
    deleted_counts["products"] = db.query(Product).filter(
        Product.workspace_id == workspace.id,
        Product.is_demo == True
    ).delete()

    # Clean vendors
    deleted_counts["vendors"] = db.query(Vendor).filter(
        Vendor.workspace_id == workspace.id,
        Vendor.is_demo == True
    ).delete()

    db.commit()

    return {
        "status": "success",
        "message": "Demo data successfully reset.",
        "workspace_id": workspace.id,
        "deleted_counts": deleted_counts
    }
