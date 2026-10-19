from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String)
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    stock_threshold = Column(Integer, default=10, nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Database-level constraints to prevent invalid data
    __table_args__ = (
        CheckConstraint('stock_quantity >= 0', name='check_stock_quantity_non_negative'),
        CheckConstraint('stock_threshold >= 0', name='check_stock_threshold_non_negative'),
        CheckConstraint('price >= 0', name='check_price_non_negative'),
    )

    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    stock_transactions = relationship("StockTransaction", back_populates="product")
    expenses = relationship("Expense", back_populates="product")
    demand_forecasts = relationship("DemandForecast", back_populates="product")
    stockout_predictions = relationship("StockoutPrediction", back_populates="product")
    restocking_recommendations = relationship("RestockingRecommendation", back_populates="product")
    dead_stock_detections = relationship("DeadStockDetection", back_populates="product")
    ai_alerts = relationship("AIAlert", back_populates="product")

