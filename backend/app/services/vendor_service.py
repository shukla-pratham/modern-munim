"""
Vendor Service
B2B: Business logic for vendor operations with row-level locking
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_, func, desc
from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.vendor import Vendor, VendorProduct, VendorPerformanceMetric
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus
from app.models.product import Product
from app.core.exceptions import ValidationError
from app.models.stock_transaction import StockTransaction, TransactionType
import logging

logger = logging.getLogger(__name__)


def lock_vendor_for_update(db: Session, vendor_id: int) -> Optional[Vendor]:
    """
    Lock vendor row for update (prevents concurrent modifications).
    Use when updating vendor scores or metrics.
    """
    return db.query(Vendor).filter(Vendor.id == vendor_id).with_for_update().first()


def lock_product_for_update(db: Session, product_id: int) -> Optional[Product]:
    """
    Lock product row for update (prevents race conditions in inventory updates).
    """
    return db.query(Product).filter(Product.id == product_id).with_for_update().first()


def create_purchase_order(
    db: Session,
    vendor_id: int,
    items: List[dict],
    workspace_id: int,
    promised_delivery_date: Optional[datetime] = None,
    is_demo: bool = False,
) -> PurchaseOrder:
    """
    Create purchase order with transaction safety and workspace isolation.
    """
    # Lock vendor for update
    vendor = lock_vendor_for_update(db, vendor_id)
    if not vendor or vendor.workspace_id != workspace_id:
        raise ValidationError(f"Vendor {vendor_id} not found")
    
    if not vendor.is_active:
        raise ValidationError(f"Vendor {vendor_id} is not active")
    
    # Calculate total cost and validate items
    total_cost = Decimal("0")
    locked_products = {}
    
    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_cost = item["unit_cost"]
        
        # Lock product for update
        product = lock_product_for_update(db, product_id)
        if not product or product.workspace_id != workspace_id:
            raise ValidationError(f"Product {product_id} not found")
        
        # Validate vendor-product relationship
        vendor_product = db.query(VendorProduct).filter(
            and_(
                VendorProduct.vendor_id == vendor_id,
                VendorProduct.product_id == product_id
            )
        ).first()
        
        if not vendor_product:
            raise ValidationError(f"Vendor {vendor_id} does not supply product {product_id}")
        
        if quantity < vendor_product.min_order_qty:
            raise ValidationError(f"Quantity {quantity} below minimum order quantity {vendor_product.min_order_qty}")
        
        item_total = Decimal(str(quantity)) * Decimal(str(unit_cost))
        total_cost += item_total
        locked_products[product_id] = product
    
    # Create purchase order
    po = PurchaseOrder(
        vendor_id=vendor_id,
        workspace_id=workspace_id,
        is_demo=is_demo,
        po_number=f"PO-{datetime.now().strftime('%Y%m%d')}-{vendor_id}-{db.query(func.max(PurchaseOrder.id)).scalar() or 0 + 1}",
        status=PurchaseOrderStatus.CREATED.value,
        total_cost=total_cost,
        promised_delivery_date=promised_delivery_date,
        order_date=datetime.now()
    )
    db.add(po)
    db.flush()  # Get PO ID
    
    # Create purchase order items
    for item in items:
        po_item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_cost=item["unit_cost"],
            total_cost=Decimal(str(item["quantity"])) * Decimal(str(item["unit_cost"]))
        )
        db.add(po_item)
    
    db.commit()
    db.refresh(po)
    
    logger.info(f"Created purchase order {po.po_number} for vendor {vendor_id} in workspace {workspace_id}")
    return po


def mark_purchase_order_delivered(
    db: Session,
    purchase_order_id: int,
    workspace_id: int,
    actual_delivery_date: Optional[datetime] = None
) -> PurchaseOrder:
    """
    Mark purchase order as delivered and update inventory scoped to workspace.
    """
    if actual_delivery_date is None:
        actual_delivery_date = datetime.now()
    
    # Lock purchase order for update
    po = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.id == purchase_order_id, PurchaseOrder.workspace_id == workspace_id)
        .with_for_update()
        .first()
    )
    if not po:
        raise ValidationError(f"Purchase order {purchase_order_id} not found")
    
    if po.status == PurchaseOrderStatus.DELIVERED.value:
        return po  # Already delivered
    
    # Calculate delay days
    delay_days = None
    if po.promised_delivery_date:
        delay = (actual_delivery_date - po.promised_delivery_date).days
        delay_days = delay if delay > 0 else 0
    
    # Update purchase order
    po.status = PurchaseOrderStatus.DELIVERED.value
    po.actual_delivery_date = actual_delivery_date
    po.delay_days = delay_days
    
    # Update inventory (with row-level locking)
    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == purchase_order_id).all()
    
    for item in items:
        product = lock_product_for_update(db, item.product_id)
        if product and product.workspace_id == workspace_id:
            product.stock_quantity += item.quantity
            
            # Create stock transaction
            from app.models.stock_transaction import StockTransaction, TransactionType
            transaction = StockTransaction(
                product_id=item.product_id,
                quantity_change=item.quantity,
                transaction_type=TransactionType.STOCK_IN,
                reason=f"Purchase order {po.po_number} delivered",
                workspace_id=workspace_id,
                is_demo=po.is_demo,
            )
            db.add(transaction)
    
    db.commit()
    db.refresh(po)
    
    logger.info(f"Marked purchase order {po.po_number} as delivered in workspace {workspace_id} (delay: {delay_days} days)")
    return po

