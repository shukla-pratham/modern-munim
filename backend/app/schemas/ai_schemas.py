from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal


class DemandForecastResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    forecast_date: date
    forecasted_quantity: Decimal
    confidence_score: Decimal
    trend: str
    created_at: datetime

    class Config:
        from_attributes = True


class StockoutPredictionResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    days_until_stockout: int
    risk_level: str
    confidence_score: Decimal
    sales_velocity: Decimal
    explanation: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RestockingRecommendationResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    recommended_quantity: int
    recommended_timing_days: int
    should_restock: str
    confidence_score: Decimal
    demand_forecast_impact: Optional[Decimal]
    margin_impact: Optional[Decimal]
    stock_risk_impact: Optional[Decimal]
    cost_impact: Optional[Decimal]
    explanation: str
    created_at: datetime

    class Config:
        from_attributes = True


class DeadStockDetectionResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    is_dead_stock: str
    risk_score: Decimal
    demand_trend: Optional[str]
    days_since_last_sale: Optional[int]
    holding_cost_ratio: Optional[Decimal]
    margin_status: Optional[str]
    suggested_action: str
    explanation: str
    created_at: datetime

    class Config:
        from_attributes = True


class AIAlertResponse(BaseModel):
    id: int
    alert_type: str
    product_id: Optional[int]
    product_name: Optional[str]
    severity: str
    title: str
    message: str
    is_read: str
    created_at: datetime

    class Config:
        from_attributes = True


class AIInsightsResponse(BaseModel):
    """Combined AI insights for a product"""
    product_id: int
    product_name: str
    demand_forecast: Optional[DemandForecastResponse]
    stockout_prediction: Optional[StockoutPredictionResponse]
    restocking_recommendation: Optional[RestockingRecommendationResponse]
    dead_stock_detection: Optional[DeadStockDetectionResponse]


class BatchProcessingSummary(BaseModel):
    products_processed: int
    forecasts_created: int
    predictions_created: int
    recommendations_created: int
    detections_created: int
    alerts_created: int
    errors: List[dict]
