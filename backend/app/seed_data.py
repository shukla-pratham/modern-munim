"""
Seed data generator for demo usage
Run with: python -m app.seed_data
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.expense import Expense, ExpenseCategory, ExpenseType
from app.models.vendor import Vendor, VendorProduct, VendorPerformanceMetric
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus
from app.models.inventory_snapshot import InventorySnapshot
from app.models.stock_transaction import StockTransaction, TransactionType
from app.models.order import Order, OrderItem, OrderStatus
from app.core.security import get_password_hash
from decimal import Decimal
from datetime import datetime, timedelta

# Note: Tables should be created via Alembic migrations, not here
# Run: alembic upgrade head

db: Session = SessionLocal()


def seed_users():
    """Create B2B users: admin, manager, and internal users"""
    # Admin user
    admin = db.query(User).filter(User.email == "admin@marketplace.com").first()
    if not admin:
        admin = User(
            email="admin@marketplace.com",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        print("Created admin user: admin@marketplace.com / admin123")
    
    # Manager user (B2B)
    manager = db.query(User).filter(User.email == "manager@marketplace.com").first()
    if not manager:
        manager = User(
            email="manager@marketplace.com",
            password_hash=get_password_hash("manager123"),
            role=UserRole.MANAGER
        )
        db.add(manager)
        print("Created manager user: manager@marketplace.com / manager123")
    
    # Internal users (for orders/records)
    internal_users = [
        ("ops@marketplace.com", "ops123", UserRole.CUSTOMER),
        ("sales@marketplace.com", "sales123", UserRole.CUSTOMER),
    ]
    
    for email, password, role in internal_users:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                password_hash=get_password_hash(password),
                role=role
            )
            db.add(user)
            print(f"Created internal user: {email} / {password}")
    
    db.commit()


def seed_products():
    """Create demo products"""
    products_data = [
        {
            "name": "Wireless Mouse",
            "description": "Ergonomic wireless mouse with 2.4GHz connectivity",
            "price": Decimal("29.99"),
            "stock_quantity": 50,
            "stock_threshold": 10
        },
        {
            "name": "Mechanical Keyboard",
            "description": "RGB mechanical keyboard with Cherry MX switches",
            "price": Decimal("129.99"),
            "stock_quantity": 30,
            "stock_threshold": 5
        },
        {
            "name": "USB-C Hub",
            "description": "7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader",
            "price": Decimal("49.99"),
            "stock_quantity": 75,
            "stock_threshold": 15
        },
        {
            "name": "Laptop Stand",
            "description": "Adjustable aluminum laptop stand for better ergonomics",
            "price": Decimal("39.99"),
            "stock_quantity": 40,
            "stock_threshold": 10
        },
        {
            "name": "Webcam HD 1080p",
            "description": "Full HD webcam with auto-focus and built-in microphone",
            "price": Decimal("79.99"),
            "stock_quantity": 25,
            "stock_threshold": 5
        },
        {
            "name": "Noise Cancelling Headphones",
            "description": "Premium wireless headphones with active noise cancellation",
            "price": Decimal("199.99"),
            "stock_quantity": 20,
            "stock_threshold": 5
        },
        {
            "name": "Monitor Stand",
            "description": "Dual monitor stand with gas spring arms",
            "price": Decimal("149.99"),
            "stock_quantity": 15,
            "stock_threshold": 3
        },
        {
            "name": "Desk Mat",
            "description": "Large desk mat with stitched edges, 36x18 inches",
            "price": Decimal("24.99"),
            "stock_quantity": 60,
            "stock_threshold": 20
        },
        {
            "name": "Cable Management Kit",
            "description": "Cable clips, ties, and sleeves for organized workspace",
            "price": Decimal("14.99"),
            "stock_quantity": 100,
            "stock_threshold": 30
        },
        {
            "name": "LED Desk Lamp",
            "description": "Adjustable LED desk lamp with touch controls and USB charging",
            "price": Decimal("34.99"),
            "stock_quantity": 35,
            "stock_threshold": 10
        },
    ]
    
    for product_data in products_data:
        existing = db.query(Product).filter(Product.name == product_data["name"]).first()
        if not existing:
            product = Product(**product_data)
            db.add(product)
            print(f"Created product: {product_data['name']}")
    
    db.commit()


def seed_expenses():
    """Create demo expenses"""
    # Get some products for product-linked expenses
    products = db.query(Product).limit(5).all()
    
    expenses_data = [
        # Inventory expenses (product-linked)
        {
            "category": ExpenseCategory.INVENTORY,
            "description": "Bulk purchase of wireless mice",
            "amount": Decimal("500.00"),
            "expense_type": ExpenseType.ONE_TIME,
            "product_id": products[0].id if products else None
        },
        {
            "category": ExpenseCategory.INVENTORY,
            "description": "Keyboard inventory restock",
            "amount": Decimal("2000.00"),
            "expense_type": ExpenseType.ONE_TIME,
            "product_id": products[1].id if len(products) > 1 else None
        },
        # Operations expenses (global)
        {
            "category": ExpenseCategory.OPERATIONS,
            "description": "Office rent - January",
            "amount": Decimal("2000.00"),
            "expense_type": ExpenseType.RECURRING,
            "product_id": None
        },
        {
            "category": ExpenseCategory.OPERATIONS,
            "description": "Utilities - January",
            "amount": Decimal("300.00"),
            "expense_type": ExpenseType.RECURRING,
            "product_id": None
        },
        {
            "category": ExpenseCategory.OPERATIONS,
            "description": "Shipping supplies",
            "amount": Decimal("150.00"),
            "expense_type": ExpenseType.ONE_TIME,
            "product_id": None
        },
        # Marketing expenses (global)
        {
            "category": ExpenseCategory.MARKETING,
            "description": "Google Ads campaign - January",
            "amount": Decimal("500.00"),
            "expense_type": ExpenseType.RECURRING,
            "product_id": None
        },
        {
            "category": ExpenseCategory.MARKETING,
            "description": "Social media advertising",
            "amount": Decimal("200.00"),
            "expense_type": ExpenseType.ONE_TIME,
            "product_id": None
        },
        {
            "category": ExpenseCategory.MARKETING,
            "description": "Email marketing platform subscription",
            "amount": Decimal("50.00"),
            "expense_type": ExpenseType.RECURRING,
            "product_id": None
        },
    ]
    
    for expense_data in expenses_data:
        expense = Expense(**expense_data)
        db.add(expense)
        print(f"Created expense: {expense_data['description']}")
    
    db.commit()


def seed_vendors():
    """Create B2B vendors with intelligence scores"""
    vendors_data = [
        {
            "name": "ReliableTech Supply",
            "is_active": True,
            "avg_lead_time_days": 7,
            "reliability_score": Decimal("85.0"),
            "cost_score": Decimal("70.0"),
            "overall_score": Decimal("79.0")
        },
        {
            "name": "BudgetParts Co.",
            "is_active": True,
            "avg_lead_time_days": 10,
            "reliability_score": Decimal("60.0"),
            "cost_score": Decimal("90.0"),
            "overall_score": Decimal("72.0")
        },
        {
            "name": "PremiumVendor Inc.",
            "is_active": True,
            "avg_lead_time_days": 5,
            "reliability_score": Decimal("95.0"),
            "cost_score": Decimal("50.0"),
            "overall_score": Decimal("77.0")
        },
        {
            "name": "RiskySupplier Ltd.",
            "is_active": True,
            "avg_lead_time_days": 14,
            "reliability_score": Decimal("45.0"),
            "cost_score": Decimal("75.0"),
            "overall_score": Decimal("57.0")
        },
        {
            "name": "Global Components Hub",
            "is_active": True,
            "avg_lead_time_days": 8,
            "reliability_score": Decimal("78.0"),
            "cost_score": Decimal("82.0"),
            "overall_score": Decimal("80.0")
        },
        {
            "name": "FastShip Logistics",
            "is_active": True,
            "avg_lead_time_days": 3,
            "reliability_score": Decimal("88.0"),
            "cost_score": Decimal("58.0"),
            "overall_score": Decimal("76.0")
        },
    ]
    
    for vendor_data in vendors_data:
        existing = db.query(Vendor).filter(Vendor.name == vendor_data["name"]).first()
        if not existing:
            vendor = Vendor(**vendor_data)
            db.add(vendor)
            print(f"Created vendor: {vendor_data['name']}")
    
    db.commit()


def seed_vendor_products():
    """Create vendor-product pricing relationships (all products, multiple vendors)"""
    vendors = db.query(Vendor).all()
    products = db.query(Product).all()
    
    if not vendors or not products:
        print("Skipping vendor products: need vendors and products first")
        return
    
    vendor_product_data = []
    # ReliableTech (0): first 6 products, competitive
    for product in products[:6]:
        vendor_product_data.append({
            "vendor_id": vendors[0].id,
            "product_id": product.id,
            "unit_cost": product.price * Decimal("0.65"),
            "min_order_qty": 10,
            "lead_time_days": 7
        })
    # BudgetParts (1): all products, cheap, higher min
    for product in products:
        vendor_product_data.append({
            "vendor_id": vendors[1].id,
            "product_id": product.id,
            "unit_cost": product.price * Decimal("0.55"),
            "min_order_qty": 20,
            "lead_time_days": 10
        })
    # PremiumVendor (2): first 8 products, expensive, low min
    for product in products[:8]:
        vendor_product_data.append({
            "vendor_id": vendors[2].id,
            "product_id": product.id,
            "unit_cost": product.price * Decimal("0.80"),
            "min_order_qty": 1,
            "lead_time_days": 5
        })
    # RiskySupplier (3): first 4 products
    for product in products[:4]:
        vendor_product_data.append({
            "vendor_id": vendors[3].id,
            "product_id": product.id,
            "unit_cost": product.price * Decimal("0.52"),
            "min_order_qty": 50,
            "lead_time_days": 14
        })
    # Global Components Hub (4): products 2–8
    for product in products[2:9] if len(products) > 9 else products[2:]:
        vendor_product_data.append({
            "vendor_id": vendors[4].id,
            "product_id": product.id,
            "unit_cost": product.price * Decimal("0.68"),
            "min_order_qty": 15,
            "lead_time_days": 8
        })
    # FastShip (5): first 5 products, fast
    for product in products[:5]:
        vendor_product_data.append({
            "vendor_id": vendors[5].id,
            "product_id": product.id,
            "unit_cost": product.price * Decimal("0.72"),
            "min_order_qty": 5,
            "lead_time_days": 3
        })
    
    for vp_data in vendor_product_data:
        existing = db.query(VendorProduct).filter(
            VendorProduct.vendor_id == vp_data["vendor_id"],
            VendorProduct.product_id == vp_data["product_id"]
        ).first()
        if not existing:
            vp = VendorProduct(**vp_data)
            db.add(vp)
            print(f"Created vendor-product: Vendor {vp_data['vendor_id']} -> Product {vp_data['product_id']}")
    
    db.commit()


def seed_vendor_performance_metrics():
    """Create vendor performance history for dashboards and trends"""
    vendors = db.query(Vendor).all()
    if not vendors:
        return
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for vendor in vendors:
        for weeks_ago in range(12, 0, -1):
            metric_date = base_date - timedelta(weeks=weeks_ago)
            existing = db.query(VendorPerformanceMetric).filter(
                VendorPerformanceMetric.vendor_id == vendor.id,
                VendorPerformanceMetric.metric_date == metric_date
            ).first()
            if not existing:
                # Vary metrics by vendor and time
                r = (vendor.id + weeks_ago) % 10
                m = VendorPerformanceMetric(
                    vendor_id=vendor.id,
                    metric_date=metric_date,
                    avg_lead_time=Decimal(str((vendor.avg_lead_time_days or 7) + (r - 5) * 0.5)),
                    on_time_delivery_rate=Decimal(str(min(100, (vendor.reliability_score or 70) + (r - 5) * 2))),
                    fulfillment_rate=Decimal(str(min(100, (vendor.reliability_score or 70) + r))),
                    avg_unit_cost=Decimal("50.00") + Decimal(str(r * 3)),
                    price_variance=Decimal(str(r)),
                    delay_days_avg=Decimal(str(max(0, r - 3)))
                )
                db.add(m)
    db.commit()
    print("Created vendor performance metrics for all vendors (12 weeks)")


def seed_purchase_orders():
    """Create B2B purchase orders with delivery performance data"""
    from sqlalchemy.exc import ProgrammingError
    vendors = db.query(Vendor).all()
    products = db.query(Product).limit(5).all()
    if not vendors or not products:
        print("Skipping purchase orders: need vendors and products first")
        return
    try:
        vendor_products = db.query(VendorProduct).all()
        vp_map = {(vp.vendor_id, vp.product_id): vp for vp in vendor_products}

        # Create purchase orders with various delivery scenarios
        po_data = [
            {
                "vendor_id": vendors[0].id,  # ReliableTech - on-time delivery
                "po_number": "PO-2026-001",
                "total_cost": Decimal("1500.00"),
                "status": PurchaseOrderStatus.DELIVERED.value,
                "order_date": datetime.now() - timedelta(days=30),
                "promised_delivery_date": datetime.now() - timedelta(days=23),
                "actual_delivery_date": datetime.now() - timedelta(days=23),
                "delay_days": 0  # On time
            },
            {
                "vendor_id": vendors[1].id,  # BudgetParts - late delivery
                "po_number": "PO-2026-002",
                "total_cost": Decimal("2200.00"),
                "status": PurchaseOrderStatus.DELIVERED.value,
                "order_date": datetime.now() - timedelta(days=25),
                "promised_delivery_date": datetime.now() - timedelta(days=15),
                "actual_delivery_date": datetime.now() - timedelta(days=12),
                "delay_days": 3  # 3 days late
            },
            {
                "vendor_id": vendors[0].id,  # ReliableTech - early delivery
                "po_number": "PO-2026-003",
                "total_cost": Decimal("3200.00"),
                "status": PurchaseOrderStatus.DELIVERED.value,
                "order_date": datetime.now() - timedelta(days=20),
                "promised_delivery_date": datetime.now() - timedelta(days=13),
                "actual_delivery_date": datetime.now() - timedelta(days=14),
                "delay_days": 0  # On time (negative = early, but we store 0)
            },
            {
                "vendor_id": vendors[3].id,  # RiskySupplier - very late
                "po_number": "PO-2026-004",
                "total_cost": Decimal("1800.00"),
                "status": PurchaseOrderStatus.DELIVERED.value,
                "order_date": datetime.now() - timedelta(days=40),
                "promised_delivery_date": datetime.now() - timedelta(days=26),
                "actual_delivery_date": datetime.now() - timedelta(days=20),
                "delay_days": 6  # 6 days late
            },
            {
                "vendor_id": vendors[2].id,  # PremiumVendor - pending order
                "po_number": "PO-2026-005",
                "total_cost": Decimal("2500.00"),
                "status": PurchaseOrderStatus.ORDERED.value,
                "order_date": datetime.now() - timedelta(days=5),
                "promised_delivery_date": datetime.now() + timedelta(days=2),
                "actual_delivery_date": None,
                "delay_days": None
            },
        ]

        for po_info in po_data:
            existing = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_info["po_number"]).first()
            if not existing:
                po = PurchaseOrder(**po_info)
                db.add(po)
                db.flush()  # Get PO ID

                vendor_id = po_info["vendor_id"]
                available_products = [p for p in products if (vendor_id, p.id) in vp_map]

                if available_products:
                    vp = vp_map[(vendor_id, available_products[0].id)]
                    items = [
                        PurchaseOrderItem(
                            purchase_order_id=po.id,
                            product_id=available_products[0].id,
                            quantity=vp.min_order_qty * 2,
                            unit_cost=vp.unit_cost,
                            total_cost=vp.unit_cost * Decimal(str(vp.min_order_qty * 2))
                        )
                    ]
                    if len(available_products) > 1:
                        vp2 = vp_map[(vendor_id, available_products[1].id)]
                        items.append(
                            PurchaseOrderItem(
                                purchase_order_id=po.id,
                                product_id=available_products[1].id,
                                quantity=vp2.min_order_qty,
                                unit_cost=vp2.unit_cost,
                                total_cost=vp2.unit_cost * Decimal(str(vp2.min_order_qty))
                            )
                        )
                    for item in items:
                        db.add(item)
                print(f"Created purchase order: {po_info['po_number']}")
        db.commit()
    except ProgrammingError as e:
        db.rollback()
        if "does not exist" in str(e):
            print("Skipping purchase orders: purchase_orders table not found (run alembic upgrade head if needed)")
        else:
            raise


def seed_inventory_snapshots():
    """Create B2B inventory snapshots for analytics"""
    from sqlalchemy.exc import ProgrammingError
    products = db.query(Product).all()
    if not products:
        print("Skipping inventory snapshots: need products first")
        return
    try:
        for days_ago in range(7, 0, -1):
            snapshot_date = datetime.now() - timedelta(days=days_ago)
            for product in products[:5]:  # Sample products
                existing = db.query(InventorySnapshot).filter(
                    InventorySnapshot.product_id == product.id,
                    InventorySnapshot.snapshot_date == snapshot_date
                ).first()
                if not existing:
                    base_qty = product.stock_quantity
                    variation = (days_ago % 3) - 1  # -1, 0, or 1
                    qty_on_hand = max(0, base_qty + variation * 5)
                    qty_reserved = 0
                    qty_available = qty_on_hand - qty_reserved
                    unit_cost = product.price * Decimal("0.6")
                    total_value = qty_on_hand * unit_cost
                    snapshot = InventorySnapshot(
                        product_id=product.id,
                        snapshot_date=snapshot_date,
                        quantity_on_hand=qty_on_hand,
                        quantity_reserved=qty_reserved,
                        quantity_available=qty_available,
                        unit_cost=unit_cost,
                        total_value=total_value,
                        days_supply=30 if qty_on_hand > 0 else 0
                    )
                    db.add(snapshot)
        db.commit()
        print(f"Created inventory snapshots for {len(products[:5])} products over 7 days")
    except ProgrammingError as e:
        db.rollback()
        if "does not exist" in str(e):
            print("Skipping inventory snapshots: inventory_snapshots table not found (run alembic upgrade head if needed)")
        else:
            raise


def seed_internal_orders():
    """Create B2B internal orders (sales records)"""
    from sqlalchemy.exc import ProgrammingError
    users = db.query(User).filter(User.role == UserRole.CUSTOMER).limit(2).all()
    products = db.query(Product).limit(3).all()
    if not users or not products:
        print("Skipping internal orders: need users and products first")
        return
    try:
        order = Order(
            user_id=users[0].id,
            total_amount=Decimal("159.98"),
            status=OrderStatus.COMPLETED,
            created_at=datetime.now() - timedelta(days=5)
        )
        db.add(order)
        db.flush()
        items = [
            OrderItem(
                order_id=order.id,
                product_id=products[0].id,
                quantity=2,
                price_at_purchase=products[0].price
            ),
            OrderItem(
                order_id=order.id,
                product_id=products[1].id,
                quantity=1,
                price_at_purchase=products[1].price
            ),
        ]
        for item in items:
            db.add(item)
        db.commit()
        print("Created internal order records")
    except ProgrammingError as e:
        db.rollback()
        if "does not exist" in str(e):
            print("Skipping internal orders: orders/order_items table not found (run alembic upgrade head if needed)")
        else:
            raise


def main():
    """Run all seed functions"""
    print("Starting B2B seed data generation...")
    print("-" * 50)
    
    seed_users()
    print("-" * 50)
    seed_products()
    print("-" * 50)
    seed_expenses()
    print("-" * 50)
    seed_vendors()
    print("-" * 50)
    seed_vendor_products()
    print("-" * 50)
    seed_vendor_performance_metrics()
    print("-" * 50)
    seed_purchase_orders()
    print("-" * 50)
    seed_inventory_snapshots()
    print("-" * 50)
    seed_internal_orders()
    print("-" * 50)
    
    print("\nB2B seed data generation completed!")
    print("\nDemo credentials:")
    print("Admin: admin@marketplace.com / admin123")
    print("Manager: manager@marketplace.com / manager123")
    print("Ops: ops@marketplace.com / ops123")


if __name__ == "__main__":
    main()
    db.close()
