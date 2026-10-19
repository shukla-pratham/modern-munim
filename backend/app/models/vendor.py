"""
Vendor Intelligence Models
B2B: Vendor management with scoring and performance tracking
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Vendor(Base):
    """
    B2B: Vendor master data with intelligence scores
    
    Scoring System:
    - reliability_score: 0-100 (higher = more reliable)
    - cost_score: 0-100 (higher = better value)
    - overall_score: 0-100 (weighted combination)
    
    Scores are computed from vendor_performance_metrics and updated periodically.
    """
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Intelligence scores (0-100, higher is better)
    avg_lead_time_days = Column(Integer, nullable=True)  # Average historical lead time
    reliability_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    cost_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    overall_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('avg_lead_time_days >= 0', name='check_vendor_lead_time_non_negative'),
        CheckConstraint('reliability_score >= 0 AND reliability_score <= 100', name='check_reliability_score_range'),
        CheckConstraint('cost_score >= 0 AND cost_score <= 100', name='check_cost_score_range'),
        CheckConstraint('overall_score >= 0 AND overall_score <= 100', name='check_overall_score_range'),
        Index('ix_vendors_overall_score', 'overall_score'),  # For ranking queries
        Index('ix_vendors_is_active_score', 'is_active', 'overall_score'),  # For active vendor rankings
    )

    # Relationships
    vendor_products = relationship("VendorProduct", back_populates="vendor", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    performance_metrics = relationship("VendorPerformanceMetric", back_populates="vendor", cascade="all, delete-orphan")


class VendorProduct(Base):
    """
    B2B: Vendor-specific product pricing and terms
    
    Links vendors to products with:
    - Unit cost (vendor-specific pricing)
    - Minimum order quantity
    - Lead time (product-specific, may differ from vendor avg)
    """
    __tablename__ = "vendor_products"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    min_order_qty = Column(Integer, default=1, nullable=False)
    lead_time_days = Column(Integer, nullable=True)  # Product-specific lead time
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('unit_cost >= 0', name='check_vendor_product_cost_non_negative'),
        CheckConstraint('min_order_qty > 0', name='check_vendor_product_min_qty_positive'),
        CheckConstraint('lead_time_days >= 0', name='check_vendor_product_lead_time_non_negative'),
        Index('ix_vendor_products_vendor_product', 'vendor_id', 'product_id'),  # For vendor-product lookups
    )

    # Relationships
    vendor = relationship("Vendor", back_populates="vendor_products")
    product = relationship("Product")


class VendorPerformanceMetric(Base):
    """
    B2B: Time-series vendor performance metrics
    
    Used for:
    - Historical trend analysis
    - Score calculation
    - Dashboard visualizations
    - AI predictions
    
    Metrics are computed from purchase order history.
    """
    __tablename__ = "vendor_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Performance metrics
    avg_lead_time = Column(Numeric(5, 2), nullable=True)  # Average lead time in days
    on_time_delivery_rate = Column(Numeric(5, 2), nullable=True)  # Percentage (0-100)
    fulfillment_rate = Column(Numeric(5, 2), nullable=True)  # Percentage (0-100)
    avg_unit_cost = Column(Numeric(10, 2), nullable=True)
    price_variance = Column(Numeric(10, 2), nullable=True)  # Standard deviation of prices
    delay_days_avg = Column(Numeric(5, 2), nullable=True)  # Average delay when late
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint('avg_lead_time >= 0', name='check_metric_lead_time_non_negative'),
        CheckConstraint('on_time_delivery_rate >= 0 AND on_time_delivery_rate <= 100', name='check_otd_rate_range'),
        CheckConstraint('fulfillment_rate >= 0 AND fulfillment_rate <= 100', name='check_fulfillment_rate_range'),
        CheckConstraint('avg_unit_cost >= 0', name='check_metric_cost_non_negative'),
        CheckConstraint('price_variance >= 0', name='check_price_variance_non_negative'),
        Index('ix_vendor_performance_vendor_date', 'vendor_id', 'metric_date'),  # Time-series queries
    )

    # Relationships
    vendor = relationship("Vendor", back_populates="performance_metrics")
