"""
API endpoints for reading AI/ML insights.
All AI computation happens in background jobs - these endpoints only read results.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_workspace, WorkspaceContext
from app.models.product import Product
from app.models.ai_forecast import (
    DemandForecast, StockoutPrediction, RestockingRecommendation,
    DeadStockDetection, AIAlert
)
from app.schemas.ai_schemas import (
    DemandForecastResponse, StockoutPredictionResponse,
    RestockingRecommendationResponse, DeadStockDetectionResponse,
    AIAlertResponse, AIInsightsResponse, BatchProcessingSummary
)
from app.services.ai_persistence_service import run_ai_batch_processing

router = APIRouter()


@router.get("/forecasts", response_model=List[DemandForecastResponse])
def get_demand_forecasts(
    product_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),  # Reduced default limit
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """
    Get demand forecasts (workspace-scoped).
    Returns latest forecasts per product if product_id not specified.
    Handles missing data gracefully.
    """
    from datetime import datetime, timedelta
    
    query = db.query(DemandForecast).join(
        Product, DemandForecast.product_id == Product.id
    ).filter(Product.workspace_id == ctx.workspace.id)
    
    if product_id:
        query = query.filter(DemandForecast.product_id == product_id)
    else:
        # Only return forecasts from last 7 days (avoid stale data)
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        query = query.filter(DemandForecast.created_at >= cutoff_date)
    
    # Get latest forecast per product if no product_id specified
    if not product_id:
        # Subquery to get latest forecast per product
        from sqlalchemy import func as sql_func
        latest_forecasts = db.query(
            DemandForecast.product_id,
            sql_func.max(DemandForecast.created_at).label('max_created_at')
        ).group_by(DemandForecast.product_id).subquery()
        
        query = query.join(
            latest_forecasts,
            (DemandForecast.product_id == latest_forecasts.c.product_id) &
            (DemandForecast.created_at == latest_forecasts.c.max_created_at)
        )
    
    forecasts = query.order_by(
        DemandForecast.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        DemandForecastResponse(
            id=f.id,
            product_id=f.product_id,
            product_name=f.product.name if f.product else "Unknown",
            forecast_date=f.forecast_date,
            forecasted_quantity=f.forecasted_quantity,
            confidence_score=f.confidence_score,
            trend=f.trend.value,
            created_at=f.created_at
        )
        for f in forecasts
    ]


@router.get("/stockout-predictions", response_model=List[StockoutPredictionResponse])
def get_stockout_predictions(
    product_id: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """Get stockout predictions (workspace-scoped)"""
    query = db.query(StockoutPrediction).join(
        Product, StockoutPrediction.product_id == Product.id
    ).filter(Product.workspace_id == ctx.workspace.id)
    
    if product_id:
        query = query.filter(StockoutPrediction.product_id == product_id)
    if risk_level:
        query = query.filter(StockoutPrediction.risk_level == risk_level)
    
    predictions = query.order_by(
        StockoutPrediction.days_until_stockout.asc()
    ).all()
    
    return [
        StockoutPredictionResponse(
            id=p.id,
            product_id=p.product_id,
            product_name=p.product.name,
            days_until_stockout=p.days_until_stockout,
            risk_level=p.risk_level,
            confidence_score=p.confidence_score,
            sales_velocity=p.sales_velocity,
            explanation=p.explanation,
            created_at=p.created_at
        )
        for p in predictions
    ]


@router.get("/restocking-recommendations", response_model=List[RestockingRecommendationResponse])
def get_restocking_recommendations(
    product_id: Optional[int] = Query(None),
    should_restock: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """Get restocking recommendations (workspace-scoped)"""
    query = db.query(RestockingRecommendation).join(
        Product, RestockingRecommendation.product_id == Product.id
    ).filter(Product.workspace_id == ctx.workspace.id)
    
    if product_id:
        query = query.filter(RestockingRecommendation.product_id == product_id)
    if should_restock:
        query = query.filter(RestockingRecommendation.should_restock == should_restock)
    
    recommendations = query.order_by(
        RestockingRecommendation.recommended_timing_days.asc()
    ).all()
    
    return [
        RestockingRecommendationResponse(
            id=r.id,
            product_id=r.product_id,
            product_name=r.product.name,
            recommended_quantity=r.recommended_quantity,
            recommended_timing_days=r.recommended_timing_days,
            should_restock=r.should_restock,
            confidence_score=r.confidence_score,
            demand_forecast_impact=r.demand_forecast_impact,
            margin_impact=r.margin_impact,
            stock_risk_impact=r.stock_risk_impact,
            cost_impact=r.cost_impact,
            explanation=r.explanation,
            created_at=r.created_at
        )
        for r in recommendations
    ]


@router.get("/dead-stock-detections", response_model=List[DeadStockDetectionResponse])
def get_dead_stock_detections(
    product_id: Optional[int] = Query(None),
    is_dead_stock: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """Get dead stock detections (workspace-scoped)"""
    query = db.query(DeadStockDetection).join(
        Product, DeadStockDetection.product_id == Product.id
    ).filter(Product.workspace_id == ctx.workspace.id)
    
    if product_id:
        query = query.filter(DeadStockDetection.product_id == product_id)
    if is_dead_stock:
        query = query.filter(DeadStockDetection.is_dead_stock == is_dead_stock)
    
    detections = query.order_by(
        DeadStockDetection.risk_score.desc()
    ).all()
    
    return [
        DeadStockDetectionResponse(
            id=d.id,
            product_id=d.product_id,
            product_name=d.product.name,
            is_dead_stock=d.is_dead_stock,
            risk_score=d.risk_score,
            demand_trend=d.demand_trend,
            days_since_last_sale=d.days_since_last_sale,
            holding_cost_ratio=d.holding_cost_ratio,
            margin_status=d.margin_status,
            suggested_action=d.suggested_action,
            explanation=d.explanation,
            created_at=d.created_at
        )
        for d in detections
    ]


@router.get("/alerts", response_model=List[AIAlertResponse])
def get_ai_alerts(
    alert_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_read: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """Get AI-generated alerts (workspace-scoped)"""
    query = db.query(AIAlert).filter(
        (AIAlert.workspace_id == ctx.workspace.id) |
        (
            AIAlert.product_id.in_(
                db.query(Product.id).filter(Product.workspace_id == ctx.workspace.id)
            )
        )
    )
    
    if alert_type:
        query = query.filter(AIAlert.alert_type == alert_type)
    if severity:
        query = query.filter(AIAlert.severity == severity)
    if is_read:
        query = query.filter(AIAlert.is_read == is_read)
    
    alerts = query.order_by(
        AIAlert.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for alert in alerts:
        product_name = None
        if alert.product_id:
            product = db.query(Product).filter(
                Product.id == alert.product_id,
                Product.workspace_id == ctx.workspace.id
            ).first()
            product_name = product.name if product else None
        
        result.append(AIAlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            product_id=alert.product_id,
            product_name=product_name,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            is_read=alert.is_read,
            created_at=alert.created_at
        ))
    
    return result


@router.put("/alerts/{alert_id}/read", response_model=AIAlertResponse)
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """Mark an alert as read (workspace-scoped)"""
    alert = db.query(AIAlert).filter(
        AIAlert.id == alert_id,
        (
            (AIAlert.workspace_id == ctx.workspace.id) |
            (
                AIAlert.product_id.in_(
                    db.query(Product.id).filter(Product.workspace_id == ctx.workspace.id)
                )
            )
        )
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = "yes"
    db.commit()
    db.refresh(alert)
    
    product_name = None
    if alert.product_id:
        product = db.query(Product).filter(
            Product.id == alert.product_id,
            Product.workspace_id == ctx.workspace.id
        ).first()
        product_name = product.name if product else None
    
    return AIAlertResponse(
        id=alert.id,
        alert_type=alert.alert_type,
        product_id=alert.product_id,
        product_name=product_name,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        is_read=alert.is_read,
        created_at=alert.created_at
    )


@router.get("/products/{product_id}/insights", response_model=AIInsightsResponse)
def get_product_ai_insights(
    product_id: int,
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """
    Get all AI insights for a specific product (workspace-scoped).
    Returns None for missing insights (handles products with no AI data gracefully).
    Only returns insights from last 7 days to avoid stale data.
    """
    from datetime import datetime, timedelta
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.workspace_id == ctx.workspace.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Only consider insights from last 7 days (avoid stale data)
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    # Get latest forecasts (only recent ones)
    forecast = db.query(DemandForecast).filter(
        DemandForecast.product_id == product_id,
        DemandForecast.created_at >= cutoff_date
    ).order_by(DemandForecast.created_at.desc()).first()
    
    # Get stockout prediction (only recent)
    prediction = db.query(StockoutPrediction).filter(
        StockoutPrediction.product_id == product_id,
        StockoutPrediction.created_at >= cutoff_date
    ).order_by(StockoutPrediction.created_at.desc()).first()
    
    # Get restocking recommendation (only recent)
    recommendation = db.query(RestockingRecommendation).filter(
        RestockingRecommendation.product_id == product_id,
        RestockingRecommendation.created_at >= cutoff_date
    ).order_by(RestockingRecommendation.created_at.desc()).first()
    
    # Get dead stock detection (only recent)
    detection = db.query(DeadStockDetection).filter(
        DeadStockDetection.product_id == product_id,
        DeadStockDetection.created_at >= cutoff_date
    ).order_by(DeadStockDetection.created_at.desc()).first()
    
    # Build response with proper None handling
    forecast_response = None
    if forecast:
        forecast_response = DemandForecastResponse(
            id=forecast.id,
            product_id=forecast.product_id,
            product_name=product.name,
            forecast_date=forecast.forecast_date,
            forecasted_quantity=forecast.forecasted_quantity,
            confidence_score=forecast.confidence_score,
            trend=forecast.trend.value,
            created_at=forecast.created_at
        )
    
    prediction_response = None
    if prediction:
        prediction_response = StockoutPredictionResponse(
            id=prediction.id,
            product_id=prediction.product_id,
            product_name=product.name,
            days_until_stockout=prediction.days_until_stockout,
            risk_level=prediction.risk_level,
            confidence_score=prediction.confidence_score,
            sales_velocity=prediction.sales_velocity,
            explanation=prediction.explanation,
            created_at=prediction.created_at
        )
    
    recommendation_response = None
    if recommendation:
        recommendation_response = RestockingRecommendationResponse(
            id=recommendation.id,
            product_id=recommendation.product_id,
            product_name=product.name,
            recommended_quantity=recommendation.recommended_quantity,
            recommended_timing_days=recommendation.recommended_timing_days,
            should_restock=recommendation.should_restock,
            confidence_score=recommendation.confidence_score,
            demand_forecast_impact=recommendation.demand_forecast_impact,
            margin_impact=recommendation.margin_impact,
            stock_risk_impact=recommendation.stock_risk_impact,
            cost_impact=recommendation.cost_impact,
            explanation=recommendation.explanation,
            created_at=recommendation.created_at
        )
    
    detection_response = None
    if detection:
        detection_response = DeadStockDetectionResponse(
            id=detection.id,
            product_id=detection.product_id,
            product_name=product.name,
            is_dead_stock=detection.is_dead_stock,
            risk_score=detection.risk_score,
            demand_trend=detection.demand_trend,
            days_since_last_sale=detection.days_since_last_sale,
            holding_cost_ratio=detection.holding_cost_ratio,
            margin_status=detection.margin_status,
            suggested_action=detection.suggested_action,
            explanation=detection.explanation,
            created_at=detection.created_at
        )
    
    return AIInsightsResponse(
        product_id=product.id,
        product_name=product.name,
        demand_forecast=forecast_response,
        stockout_prediction=prediction_response,
        restocking_recommendation=recommendation_response,
        dead_stock_detection=detection_response
    )


@router.post("/batch-process", response_model=BatchProcessingSummary)
def trigger_batch_processing(
    product_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """
    Manually trigger AI batch processing (workspace-scoped).
    """
    if product_ids:
        # Validate all products belong to workspace
        valid_products = db.query(Product.id).filter(
            Product.id.in_(product_ids),
            Product.workspace_id == ctx.workspace.id
        ).all()
        scoped_ids = [p[0] for p in valid_products]
    else:
        scoped_ids = [p[0] for p in db.query(Product.id).filter(Product.workspace_id == ctx.workspace.id).all()]
    
    summary = run_ai_batch_processing(db, product_ids=scoped_ids)
    return BatchProcessingSummary(**summary)
