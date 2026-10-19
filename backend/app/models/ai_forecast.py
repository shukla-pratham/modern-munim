from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TrendType(str, enum.Enum):
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"


class DemandForecast(Base):
    """Stores demand forecasts for products"""
    __tablename__ = "demand_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    forecast_date = Column(DateTime(timezone=True), nullable=False, index=True)  # Date being forecasted
    forecasted_quantity = Column(Numeric(10, 2), nullable=False)  # Predicted demand
    confidence_score = Column(Numeric(5, 2), nullable=False)  # 0-100 confidence
    trend = Column(
        SQLEnum(
            TrendType,
            name="trendtype",
            values_callable=lambda x: [e.value for e in x],
            create_type=False,
        ),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Index for efficient queries: product + created_at for latest forecasts
    __table_args__ = (
        {'comment': 'Stores AI-generated demand forecasts. Indexed for fast retrieval of latest forecasts per product.'},
    )
    
    # Relationships
    product = relationship("Product", back_populates="demand_forecasts")


class StockoutPrediction(Base):
    """Predicts when products will run out of stock"""
    __tablename__ = "stockout_predictions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    days_until_stockout = Column(Integer, nullable=False)  # Predicted days until stockout
    risk_level = Column(String, nullable=False)  # low, medium, high
    confidence_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    sales_velocity = Column(Numeric(10, 2), nullable=False)  # Units sold per day
    explanation = Column(Text)  # Why this prediction
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    product = relationship("Product", back_populates="stockout_predictions")


class RestockingRecommendation(Base):
    """AI-powered restocking recommendations"""
    __tablename__ = "restocking_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    recommended_quantity = Column(Integer, nullable=False)
    recommended_timing_days = Column(Integer, nullable=False)  # Days until restock needed
    should_restock = Column(String, nullable=False)  # yes, no, urgent
    confidence_score = Column(Numeric(5, 2), nullable=False)
    
    # Decision factors (for explainability)
    demand_forecast_impact = Column(Numeric(5, 2))  # How much demand forecast influenced decision
    margin_impact = Column(Numeric(5, 2))  # How much profit margin influenced decision
    stock_risk_impact = Column(Numeric(5, 2))  # How much stockout risk influenced decision
    cost_impact = Column(Numeric(5, 2))  # How much holding cost influenced decision
    
    explanation = Column(Text, nullable=False)  # Human-readable explanation
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    product = relationship("Product", back_populates="restocking_recommendations")


class DeadStockDetection(Base):
    """Identifies products that should be cleared or discontinued"""
    __tablename__ = "dead_stock_detections"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    is_dead_stock = Column(String, nullable=False)  # yes, warning, no
    risk_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    
    # Detection factors
    demand_trend = Column(String)  # declining, stable, rising
    days_since_last_sale = Column(Integer)
    holding_cost_ratio = Column(Numeric(5, 2))  # Holding cost vs revenue
    margin_status = Column(String)  # negative, low, healthy
    
    suggested_action = Column(String)  # clearance, discount, stop_ordering, monitor
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    product = relationship("Product", back_populates="dead_stock_detections")


class AIAlert(Base):
    """Stores AI-generated alerts for admins"""
    __tablename__ = "ai_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, nullable=False, index=True)  # stockout, dead_stock, low_margin, etc.
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    severity = Column(String, nullable=False)  # low, medium, high, critical
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(String, default="no", nullable=False)  # yes, no
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    product = relationship("Product", back_populates="ai_alerts")
