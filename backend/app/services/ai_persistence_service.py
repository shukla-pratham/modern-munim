"""
Service for persisting AI outputs to the database.
Separates ML computation from data persistence.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app.models.product import Product
from app.models.ai_forecast import (
    DemandForecast, StockoutPrediction, RestockingRecommendation,
    DeadStockDetection, AIAlert, TrendType
)
from app.services.ml_service import (
    forecast_demand_prophet, detect_trend, predict_stockout,
    recommend_restocking, detect_dead_stock
)


def persist_demand_forecasts(db: Session, product_id: int, horizon_days: int = 30) -> List[DemandForecast]:
    """
    Generate and persist demand forecasts for a product.
    Returns list of created forecast records.
    """
    # Get sales data
    from app.services.ml_service import get_sales_time_series
    sales_data = get_sales_time_series(db, product_id, days=90)
    
    if len(sales_data) == 0:
        return []  # No sales data available
    
    # Detect overall trend
    trend, trend_confidence = detect_trend(sales_data)
    
    # Generate forecasts
    forecasts_data = forecast_demand_prophet(sales_data, horizon_days=horizon_days)
    
    # Delete old forecasts for this product
    db.query(DemandForecast).filter(
        DemandForecast.product_id == product_id,
        DemandForecast.forecast_date >= datetime.utcnow().date()
    ).delete()
    
    # Create new forecasts
    forecasts = []
    for forecast_data in forecasts_data:
        forecast = DemandForecast(
            product_id=product_id,
            forecast_date=forecast_data['date'],
            forecasted_quantity=forecast_data['quantity'],
            confidence_score=forecast_data['confidence'],
            trend=trend
        )
        db.add(forecast)
        forecasts.append(forecast)
    
    db.commit()
    return forecasts


def persist_stockout_prediction(db: Session, product_id: int) -> Optional[StockoutPrediction]:
    """
    Generate and persist stockout prediction for a product.
    """
    prediction_data = predict_stockout(db, product_id)
    if not prediction_data:
        return None
    
    # Delete old prediction
    db.query(StockoutPrediction).filter(
        StockoutPrediction.product_id == product_id
    ).delete()
    
    # Create new prediction
    prediction = StockoutPrediction(
        product_id=product_id,
        days_until_stockout=prediction_data['days_until_stockout'],
        risk_level=prediction_data['risk_level'],
        confidence_score=prediction_data['confidence'],
        sales_velocity=prediction_data['sales_velocity'],
        explanation=prediction_data['explanation']
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def persist_restocking_recommendation(db: Session, product_id: int) -> Optional[RestockingRecommendation]:
    """
    Generate and persist restocking recommendation for a product.
    """
    recommendation_data = recommend_restocking(db, product_id)
    if not recommendation_data:
        return None
    
    # Delete old recommendation
    db.query(RestockingRecommendation).filter(
        RestockingRecommendation.product_id == product_id
    ).delete()
    
    # Create new recommendation
    recommendation = RestockingRecommendation(
        product_id=product_id,
        recommended_quantity=recommendation_data['recommended_quantity'],
        recommended_timing_days=recommendation_data['recommended_timing_days'],
        should_restock=recommendation_data['should_restock'],
        confidence_score=recommendation_data['confidence'],
        demand_forecast_impact=recommendation_data['demand_forecast_impact'],
        margin_impact=recommendation_data['margin_impact'],
        stock_risk_impact=recommendation_data['stock_risk_impact'],
        cost_impact=recommendation_data['cost_impact'],
        explanation=recommendation_data['explanation']
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


def persist_dead_stock_detection(db: Session, product_id: int) -> Optional[DeadStockDetection]:
    """
    Generate and persist dead stock detection for a product.
    """
    detection_data = detect_dead_stock(db, product_id)
    if not detection_data:
        return None
    
    # Delete old detection
    db.query(DeadStockDetection).filter(
        DeadStockDetection.product_id == product_id
    ).delete()
    
    # Create new detection
    detection = DeadStockDetection(
        product_id=product_id,
        is_dead_stock=detection_data['is_dead_stock'],
        risk_score=detection_data['risk_score'],
        demand_trend=detection_data['demand_trend'],
        days_since_last_sale=detection_data['days_since_last_sale'],
        holding_cost_ratio=detection_data['holding_cost_ratio'],
        margin_status=detection_data['margin_status'],
        suggested_action=detection_data['suggested_action'],
        explanation=detection_data['explanation']
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


def create_ai_alert(
    db: Session,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    product_id: Optional[int] = None
) -> AIAlert:
    """
    Create an AI-generated alert.
    """
    alert = AIAlert(
        alert_type=alert_type,
        product_id=product_id,
        severity=severity,
        title=title,
        message=message,
        is_read="no"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def generate_alerts_from_predictions(db: Session) -> List[AIAlert]:
    """
    Generate alerts based on AI predictions.
    Called after batch processing to create actionable alerts.
    """
    alerts = []
    
    # Check stockout predictions
    high_risk_stockouts = db.query(StockoutPrediction).join(
        Product, StockoutPrediction.product_id == Product.id
    ).filter(
        StockoutPrediction.risk_level == "high",
        StockoutPrediction.days_until_stockout <= 7
    ).all()
    
    for prediction in high_risk_stockouts:
        alert = create_ai_alert(
            db,
            alert_type="stockout",
            severity="high",
            title=f"Urgent: {prediction.product.name} may stockout soon",
            message=f"{prediction.product.name} is predicted to run out of stock in {prediction.days_until_stockout} days. {prediction.explanation}",
            product_id=prediction.product_id
        )
        alerts.append(alert)
    
    # Check dead stock
    dead_stocks = db.query(DeadStockDetection).join(
        Product, DeadStockDetection.product_id == Product.id
    ).filter(
        DeadStockDetection.is_dead_stock == "yes"
    ).all()
    
    for detection in dead_stocks:
        alert = create_ai_alert(
            db,
            alert_type="dead_stock",
            severity="medium",
            title=f"Dead Stock Alert: {detection.product.name}",
            message=f"{detection.product.name} has been identified as dead stock. {detection.explanation}",
            product_id=detection.product_id
        )
        alerts.append(alert)
    
    # Check low margin products with high demand
    from app.services.ml_service import calculate_product_margin
    low_margin_high_demand = db.query(RestockingRecommendation).join(
        Product, RestockingRecommendation.product_id == Product.id
    ).filter(
        RestockingRecommendation.should_restock.in_(["yes", "urgent"])
    ).all()
    
    for rec in low_margin_high_demand:
        margin_data = calculate_product_margin(db, rec.product_id, days=30)
        if margin_data['margin_percentage'] < 10 and margin_data['margin_percentage'] > 0:
            alert = create_ai_alert(
                db,
                alert_type="low_margin",
                severity="low",
                title=f"Low Margin Alert: {rec.product.name}",
                message=f"{rec.product.name} has low margin ({margin_data['margin_percentage']:.2f}%) but high demand. Consider reviewing pricing.",
                product_id=rec.product_id
            )
            alerts.append(alert)
    
    return alerts


def run_ai_batch_processing(db: Session, product_ids: Optional[List[int]] = None, include_vendor_intelligence: bool = True) -> Dict:
    """
    Run batch AI processing for all products or specified products.
    Returns summary of what was processed.
    
    Uses per-product error handling so one failure doesn't break the entire job.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if product_ids is None:
        # Process all products
        products = db.query(Product).all()
        product_ids = [p.id for p in products]
    
    summary = {
        'products_processed': 0,
        'forecasts_created': 0,
        'predictions_created': 0,
        'recommendations_created': 0,
        'detections_created': 0,
        'alerts_created': 0,
        'errors': []
    }
    
    logger.info(f"Starting batch processing for {len(product_ids)} products")
    
    for product_id in product_ids:
        try:
            # Verify product still exists
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Product {product_id} not found, skipping")
                continue
            
            # Generate forecasts (may return empty list if no sales data)
            forecasts = persist_demand_forecasts(db, product_id, horizon_days=30)
            summary['forecasts_created'] += len(forecasts)
            
            # Generate stockout prediction (handles products with no sales)
            try:
                prediction = persist_stockout_prediction(db, product_id)
                if prediction:
                    summary['predictions_created'] += 1
            except Exception as e:
                logger.warning(f"Failed to generate stockout prediction for product {product_id}: {e}")
                summary['errors'].append({
                    'product_id': product_id,
                    'operation': 'stockout_prediction',
                    'error': str(e)
                })
            
            # Generate restocking recommendation
            try:
                recommendation = persist_restocking_recommendation(db, product_id)
                if recommendation:
                    summary['recommendations_created'] += 1
            except Exception as e:
                logger.warning(f"Failed to generate restocking recommendation for product {product_id}: {e}")
                summary['errors'].append({
                    'product_id': product_id,
                    'operation': 'restocking_recommendation',
                    'error': str(e)
                })
            
            # Detect dead stock
            try:
                detection = persist_dead_stock_detection(db, product_id)
                if detection:
                    summary['detections_created'] += 1
            except Exception as e:
                logger.warning(f"Failed to detect dead stock for product {product_id}: {e}")
                summary['errors'].append({
                    'product_id': product_id,
                    'operation': 'dead_stock_detection',
                    'error': str(e)
                })
            
            summary['products_processed'] += 1
            
            # Commit after each product to prevent rollback of all work on error
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing product {product_id}: {e}", exc_info=True)
            summary['errors'].append({
                'product_id': product_id,
                'operation': 'general',
                'error': str(e)
            })
            # Rollback only this product's changes
            db.rollback()
            # Continue with next product
    
    # Generate alerts (after all products processed)
    try:
        alerts = generate_alerts_from_predictions(db)
        summary['alerts_created'] = len(alerts)
        db.commit()
    except Exception as e:
        logger.error(f"Error generating alerts: {e}", exc_info=True)
        summary['errors'].append({
            'product_id': None,
            'operation': 'alert_generation',
            'error': str(e)
        })
        db.rollback()
    
    # Process vendor intelligence (B2B)
    if include_vendor_intelligence:
        try:
            from app.services.vendor_ai import process_vendor_intelligence_batch
            vendor_summary = process_vendor_intelligence_batch(db)
            
            # Merge vendor summary into main summary
            summary['vendors_processed'] = vendor_summary.get('vendors_processed', 0)
            summary['vendor_metrics_computed'] = vendor_summary.get('metrics_computed', 0)
            summary['vendor_scores_updated'] = vendor_summary.get('scores_updated', 0)
            summary['vendor_switch_recommendations'] = vendor_summary.get('switch_recommendations', 0)
            summary['alerts_created'] += vendor_summary.get('alerts_created', 0)
            summary['errors'].extend(vendor_summary.get('errors', []))
            
            logger.info(f"Vendor intelligence processing completed: {vendor_summary}")
        except Exception as e:
            logger.error(f"Error processing vendor intelligence: {e}", exc_info=True)
            summary['errors'].append({
                'product_id': None,
                'operation': 'vendor_intelligence',
                'error': str(e)
            })
    
    logger.info(f"Batch processing completed: {summary['products_processed']} products processed, {len(summary['errors'])} errors")
    return summary
