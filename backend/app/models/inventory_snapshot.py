from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class InventorySnapshot(Base):
    """B2B: Time-series inventory snapshots for analytics and planning"""
    __tablename__ = "inventory_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)
    quantity_on_hand = Column(Integer, nullable=False)
    quantity_reserved = Column(Integer, default=0, nullable=False)
    quantity_available = Column(Integer, nullable=False)  # on_hand - reserved
    unit_cost = Column(Numeric(10, 2), nullable=True)  # Average cost at snapshot time
    total_value = Column(Numeric(10, 2), nullable=True)  # quantity * unit_cost
    days_supply = Column(Integer, nullable=True)  # Estimated days until stockout
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint('quantity_on_hand >= 0', name='check_snapshot_on_hand_non_negative'),
        CheckConstraint('quantity_reserved >= 0', name='check_snapshot_reserved_non_negative'),
        CheckConstraint('quantity_available >= 0', name='check_snapshot_available_non_negative'),
        CheckConstraint('unit_cost >= 0', name='check_snapshot_unit_cost_non_negative'),
        CheckConstraint('total_value >= 0', name='check_snapshot_total_value_non_negative'),
        Index('ix_inventory_snapshots_product_date', 'product_id', 'snapshot_date'),  # Analytics queries
    )

    # Relationships
    product = relationship("Product")
