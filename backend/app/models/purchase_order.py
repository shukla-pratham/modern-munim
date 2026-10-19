from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, CheckConstraint, Index, Computed, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, case
from sqlalchemy.dialects.postgresql import ENUM
from app.core.database import Base
import enum


class PurchaseOrderStatus(str, enum.Enum):
    """B2B: Purchase order status enum"""
    CREATED = "created"
    ORDERED = "ordered"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    """
    B2B: Purchase orders for inventory procurement (internal)
    
    Tracks vendor orders with delivery performance metrics.
    delay_days is computed: actual_delivery_date - promised_delivery_date (if late)
    """
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    po_number = Column(String, unique=True, nullable=False, index=True)  # Purchase order number
    status = Column(String, default=PurchaseOrderStatus.CREATED.value, nullable=False, index=True)
    total_cost = Column(Numeric(10, 2), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    
    # Delivery tracking
    order_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    promised_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Computed delay (positive = late, negative = early, null = not delivered)
    delay_days = Column(Integer, nullable=True)  # Computed: actual - promised (in days)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('total_cost >= 0', name='check_po_cost_non_negative'),
        Index('ix_purchase_orders_vendor_status', 'vendor_id', 'status'),  # For vendor performance queries
        Index('ix_purchase_orders_delivery_dates', 'promised_delivery_date', 'actual_delivery_date'),  # For delay analysis
    )

    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    """
    B2B: Items within a purchase order
    
    Links purchase orders to products with quantity and cost.
    Used for inventory updates and cost tracking.
    """
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_po_item_quantity_positive'),
        CheckConstraint('unit_cost >= 0', name='check_po_item_cost_non_negative'),
        CheckConstraint('total_cost >= 0', name='check_po_item_total_non_negative'),
        Index('ix_purchase_order_items_product', 'product_id'),  # For product-based vendor analysis
    )

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
