"""
ML Service Layer - Phase 2
Provides demand forecasting, trend detection, and intelligent recommendations.
Uses batch processing and stores all outputs in the database.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.expense import Expense
from app.models.ai_forecast import (
    DemandForecast, StockoutPrediction, RestockingRecommendation,
    DeadStockDetection, TrendType
)


def get_sales_time_series(db: Session, product_id: int, days: int = 90) -> pd.DataFrame:
    """
    Extract daily sales data for a product as a time series.
    Returns DataFrame with columns: ds (date), y (quantity sold)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily sales
    sales_data = db.query(
        func.date(Order.created_at).label("date"),
        func.sum(OrderItem.quantity).label("quantity")
    ).join(
        OrderItem, Order.id == OrderItem.order_id
    ).filter(
        OrderItem.product_id == product_id,
        Order.status == OrderStatus.COMPLETED,
        Order.created_at >= cutoff_date
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()
    
    if not sales_data:
        return pd.DataFrame(columns=['ds', 'y'])
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {'ds': row.date, 'y': float(row.quantity or 0)}
        for row in sales_data
    ])
    
    # Fill missing dates with 0
    date_range = pd.date_range(start=df['ds'].min(), end=df['ds'].max(), freq='D')
    df = df.set_index('ds').reindex(date_range, fill_value=0).reset_index()
    df.columns = ['ds', 'y']
    
    return df


def detect_trend(sales_data: pd.DataFrame) -> Tuple[TrendType, float]:
    """
    Detect demand trend using linear regression on recent sales.
    Returns (trend_type, confidence_score)
    """
    if len(sales_data) < 7:
        return TrendType.STABLE, 50.0
    
    # Use last 30 days for trend detection
    recent_data = sales_data.tail(30) if len(sales_data) >= 30 else sales_data
    
    if len(recent_data) < 3:
        return TrendType.STABLE, 50.0
    
    # Simple linear regression
    x = np.arange(len(recent_data))
    y = recent_data['y'].values
    
    # Calculate slope
    slope = np.polyfit(x, y, 1)[0]
    
    # Calculate confidence based on R-squared
    y_mean = np.mean(y)
    ss_tot = np.sum((y - y_mean) ** 2)
    ss_res = np.sum((y - (slope * x + np.mean(y - slope * x))) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    confidence = max(50.0, min(95.0, r_squared * 100))
    
    # Determine trend
    avg_daily = np.mean(y)
    if avg_daily == 0:
        return TrendType.STABLE, confidence
    
    # Trend threshold: 10% change
    trend_threshold = avg_daily * 0.1
    
    if slope > trend_threshold:
        return TrendType.RISING, confidence
    elif slope < -trend_threshold:
        return TrendType.DECLINING, confidence
    else:
        return TrendType.STABLE, confidence


def forecast_demand_simple(sales_data: pd.DataFrame, horizon_days: int = 30) -> List[Dict]:
    """
    Simple demand forecasting using moving average and trend.
    Returns list of forecasts: [{date, quantity, confidence}, ...]
    """
    if len(sales_data) < 7:
        # Not enough data - use average
        avg_demand = sales_data['y'].mean() if len(sales_data) > 0 else 0
        forecasts = []
        for i in range(horizon_days):
            date = datetime.utcnow().date() + timedelta(days=i+1)
            forecasts.append({
                'date': date,
                'quantity': float(avg_demand),
                'confidence': 30.0  # Low confidence with little data
            })
        return forecasts
    
    # Calculate moving average (7-day window)
    window = min(7, len(sales_data))
    ma = sales_data['y'].tail(window).mean()
    
    # Detect trend
    trend, trend_confidence = detect_trend(sales_data)
    
    # Adjust forecast based on trend
    trend_factor = 1.0
    if trend == TrendType.RISING:
        trend_factor = 1.1  # 10% increase
    elif trend == TrendType.DECLINING:
        trend_factor = 0.9  # 10% decrease
    
    base_forecast = ma * trend_factor
    
    # Generate forecasts
    forecasts = []
    for i in range(horizon_days):
        date = datetime.utcnow().date() + timedelta(days=i+1)
        # Confidence decreases over time
        confidence = max(30.0, trend_confidence * (1 - i * 0.02))
        forecasts.append({
            'date': date,
            'quantity': float(max(0, base_forecast)),
            'confidence': confidence
        })
    
    return forecasts


def forecast_demand_prophet(sales_data: pd.DataFrame, horizon_days: int = 30) -> List[Dict]:
    """
    Demand forecasting using Facebook Prophet (if available).
    Falls back to simple forecasting if Prophet fails.
    """
    try:
        from prophet import Prophet
        
        if len(sales_data) < 14:  # Need at least 2 weeks of data
            return forecast_demand_simple(sales_data, horizon_days)
        
        # Prepare data for Prophet
        df = sales_data.copy()
        df['ds'] = pd.to_datetime(df['ds'])
        
        # Initialize and fit model
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05  # Less sensitive to changes
        )
        model.fit(df)
        
        # Make future predictions
        future = model.make_future_dataframe(periods=horizon_days)
        forecast = model.predict(future)
        
        # Extract future forecasts
        future_forecasts = forecast.tail(horizon_days)
        
        forecasts = []
        for _, row in future_forecasts.iterrows():
            forecasts.append({
                'date': row['ds'].date(),
                'quantity': float(max(0, row['yhat'])),
                'confidence': float(min(95.0, max(50.0, 100 - abs(row['yhat_upper'] - row['yhat_lower']) / max(1, row['yhat']) * 50)))
            })
        
        return forecasts
        
    except ImportError:
        # Prophet not available, use simple method
        return forecast_demand_simple(sales_data, horizon_days)
    except Exception as e:
        # If Prophet fails, fall back to simple method
        print(f"Prophet forecasting failed: {e}, using simple method")
        return forecast_demand_simple(sales_data, horizon_days)


def calculate_sales_velocity(db: Session, product_id: int, days: int = 30) -> float:
    """
    Calculate average units sold per day.
    Returns 0.0 if no sales data available (handles products with no sales history).
    """
    if days <= 0:
        return 0.0
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    total_sold = db.query(func.sum(OrderItem.quantity)).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        OrderItem.product_id == product_id,
        Order.status == OrderStatus.COMPLETED,
        Order.created_at >= cutoff_date
    ).scalar() or 0
    
    # Handle case where total_sold might be None
    if total_sold is None:
        return 0.0
    
    return float(total_sold) / days


def predict_stockout(db: Session, product_id: int) -> Optional[Dict]:
    """
    Predict days until stockout based on sales velocity.
    Returns prediction with explanation.
    Handles edge cases: products with no sales, zero stock, etc.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    current_stock = product.stock_quantity
    
    # Edge case: Already out of stock
    if current_stock == 0:
        return {
            'days_until_stockout': 0,
            'risk_level': 'critical',
            'confidence': 100.0,
            'sales_velocity': 0.0,
            'explanation': 'Product is already out of stock.'
        }
    
    # Calculate sales velocity (units per day)
    sales_velocity = calculate_sales_velocity(db, product_id, days=30)
    
    # Edge case: No sales history
    if sales_velocity == 0:
        return {
            'days_until_stockout': 999,  # Effectively never (or unknown)
            'risk_level': 'low',
            'confidence': 30.0,  # Low confidence due to no data
            'sales_velocity': 0.0,
            'explanation': 'No recent sales detected. Product may be slow-moving, new, or discontinued. Unable to predict stockout timing.'
        }
    
    # Predict days until stockout
    days_until_stockout = int(current_stock / sales_velocity) if sales_velocity > 0 else 999
    
    # Determine risk level
    if days_until_stockout <= 7:
        risk_level = 'high'
    elif days_until_stockout <= 14:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    # Confidence based on data quality and sales volume
    # More sales data = higher confidence
    days_with_sales = db.query(func.count(func.distinct(func.date(Order.created_at)))).join(
        OrderItem, Order.id == OrderItem.order_id
    ).filter(
        OrderItem.product_id == product_id,
        Order.status == OrderStatus.COMPLETED,
        Order.created_at >= datetime.utcnow() - timedelta(days=30)
    ).scalar() or 0
    
    confidence = min(95.0, max(50.0, 50.0 + (days_with_sales * 1.5)))
    
    explanation = (
        f"Current stock: {current_stock} units. "
        f"Average sales velocity: {sales_velocity:.2f} units/day. "
        f"Predicted stockout in {days_until_stockout} days."
    )
    
    return {
        'days_until_stockout': days_until_stockout,
        'risk_level': risk_level,
        'confidence': confidence,
        'sales_velocity': sales_velocity,
        'explanation': explanation
    }


def calculate_product_margin(db: Session, product_id: int, days: int = 30) -> Dict:
    """
    Calculate product profit margin considering expenses.
    Returns: {revenue, expenses, profit, margin_percentage}
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Calculate revenue
    revenue = db.query(func.sum(OrderItem.quantity * OrderItem.price_at_purchase)).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        OrderItem.product_id == product_id,
        Order.status == OrderStatus.COMPLETED,
        Order.created_at >= cutoff_date
    ).scalar() or Decimal("0.00")
    
    # Calculate product-linked expenses
    expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.product_id == product_id,
        Expense.created_at >= cutoff_date
    ).scalar() or Decimal("0.00")
    
    # Calculate profit
    profit = revenue - expenses
    
    # Calculate margin
    margin = (profit / revenue * 100) if revenue > 0 else Decimal("0.00")
    
    return {
        'revenue': float(revenue),
        'expenses': float(expenses),
        'profit': float(profit),
        'margin_percentage': float(margin)
    }


def recommend_restocking(
    db: Session,
    product_id: int,
    forecast_horizon_days: int = 30,
    lead_time_days: int = 7,
    holding_cost_rate: float = 0.02  # 2% per month
) -> Dict:
    """
    Generate intelligent restocking recommendation.
    Considers demand forecast, stockout risk, profit margin, and costs.
    Returns recommendation with explanation.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    # Get sales data
    sales_data = get_sales_time_series(db, product_id, days=90)
    
    # Forecast demand
    forecasts = forecast_demand_prophet(sales_data, horizon_days=forecast_horizon_days)
    total_forecasted_demand = sum(f['quantity'] for f in forecasts)
    avg_daily_forecast = total_forecasted_demand / forecast_horizon_days if forecast_horizon_days > 0 else 0
    
    # Get stockout prediction
    stockout_pred = predict_stockout(db, product_id)
    
    # Get margin data
    margin_data = calculate_product_margin(db, product_id, days=30)
    
    # Calculate decision factors
    current_stock = product.stock_quantity
    stock_threshold = product.stock_threshold
    
    # Factor 1: Demand forecast impact (0-100)
    demand_impact = min(100.0, (total_forecasted_demand / max(1, current_stock)) * 20)
    
    # Factor 2: Margin impact (0-100, higher margin = higher impact)
    margin_impact = max(0.0, min(100.0, margin_data['margin_percentage']))
    
    # Factor 3: Stockout risk impact (0-100)
    if stockout_pred['risk_level'] == 'high':
        stock_risk_impact = 90.0
    elif stockout_pred['risk_level'] == 'medium':
        stock_risk_impact = 60.0
    else:
        stock_risk_impact = 30.0
    
    # Factor 4: Cost impact (negative if holding cost is high relative to margin)
    holding_cost = (current_stock * float(product.price) * holding_cost_rate) / 30  # Daily holding cost
    cost_impact = max(-50.0, min(50.0, (margin_data['profit'] - holding_cost * 30) / max(1, margin_data['revenue']) * 100))
    
    # Decision logic
    should_restock = "no"
    recommended_quantity = 0
    recommended_timing = 0
    
    # Check if product is profitable
    is_profitable = margin_data['margin_percentage'] > 0
    
    # Check if we need to restock based on stockout risk
    needs_restock_for_stockout = stockout_pred['days_until_stockout'] <= (lead_time_days + 7)
    
    # Check if demand is sufficient
    has_demand = avg_daily_forecast > 0.1
    
    if not is_profitable and not needs_restock_for_stockout:
        explanation = (
            f"Product has negative margin ({margin_data['margin_percentage']:.2f}%). "
            f"Not recommending restock unless urgent stockout risk exists. "
            f"Consider reviewing pricing or costs."
        )
        should_restock = "no"
    elif needs_restock_for_stockout and has_demand:
        # Calculate recommended quantity
        days_to_cover = forecast_horizon_days
        safety_stock = stock_threshold * 2  # 2x threshold as safety
        recommended_quantity = int((avg_daily_forecast * days_to_cover) + safety_stock - current_stock)
        recommended_quantity = max(0, recommended_quantity)
        
        recommended_timing = max(0, stockout_pred['days_until_stockout'] - lead_time_days)
        
        if recommended_quantity > 0:
            if stockout_pred['risk_level'] == 'high':
                should_restock = "urgent"
            else:
                should_restock = "yes"
            
            explanation = (
                f"Recommended restock: {recommended_quantity} units within {recommended_timing} days. "
                f"Forecasted demand: {total_forecasted_demand:.1f} units over {forecast_horizon_days} days. "
                f"Current stock: {current_stock} units. "
                f"Stockout risk: {stockout_pred['risk_level']}. "
                f"Margin: {margin_data['margin_percentage']:.2f}%."
            )
        else:
            should_restock = "no"
            explanation = (
                f"Sufficient stock available. Current: {current_stock} units, "
                f"forecasted demand: {total_forecasted_demand:.1f} units."
            )
    elif not has_demand:
        explanation = (
            f"Low or no forecasted demand ({avg_daily_forecast:.2f} units/day). "
            f"Not recommending restock. Monitor for demand changes."
        )
        should_restock = "no"
    else:
        explanation = (
            f"Stock levels adequate. Current: {current_stock} units, "
            f"threshold: {stock_threshold} units. "
            f"Stockout predicted in {stockout_pred['days_until_stockout']} days."
        )
        should_restock = "no"
    
    # Calculate overall confidence
    confidence = (
        (demand_impact * 0.3 + stock_risk_impact * 0.3 + 
         margin_impact * 0.2 + (cost_impact + 50) * 0.2) / 100 * 100
    )
    confidence = max(50.0, min(95.0, confidence))
    
    return {
        'recommended_quantity': recommended_quantity,
        'recommended_timing_days': recommended_timing,
        'should_restock': should_restock,
        'confidence': confidence,
        'demand_forecast_impact': demand_impact,
        'margin_impact': margin_impact,
        'stock_risk_impact': stock_risk_impact,
        'cost_impact': cost_impact,
        'explanation': explanation
    }


def detect_dead_stock(db: Session, product_id: int) -> Dict:
    """
    Detect if a product is dead stock (slow-moving, unprofitable, etc.)
    Returns detection result with suggested actions.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    # Get sales data
    sales_data = get_sales_time_series(db, product_id, days=90)
    
    # Detect trend
    trend, _ = detect_trend(sales_data)
    
    # Calculate days since last sale
    if len(sales_data) > 0 and sales_data['y'].sum() > 0:
        last_sale_idx = sales_data[sales_data['y'] > 0].index[-1] if len(sales_data[sales_data['y'] > 0]) > 0 else None
        if last_sale_idx is not None:
            last_sale_date = sales_data.iloc[last_sale_idx]['ds']
            days_since_last_sale = (datetime.utcnow().date() - last_sale_date).days
        else:
            days_since_last_sale = 999
    else:
        days_since_last_sale = 999
    
    # Get margin data
    margin_data = calculate_product_margin(db, product_id, days=90)
    
    # Calculate holding cost ratio
    holding_cost = float(product.price) * product.stock_quantity * 0.02 / 30  # Daily holding cost
    revenue_90d = margin_data['revenue']
    holding_cost_ratio = (holding_cost * 90) / revenue_90d if revenue_90d > 0 else 999
    
    # Determine dead stock status
    is_dead_stock = "no"
    risk_score = 0.0
    suggested_action = "monitor"
    
    # Risk factors
    risk_factors = []
    
    if days_since_last_sale > 60:
        risk_score += 40
        risk_factors.append(f"No sales in {days_since_last_sale} days")
    
    if trend == TrendType.DECLINING:
        risk_score += 20
        risk_factors.append("Declining demand trend")
    
    if margin_data['margin_percentage'] < 0:
        risk_score += 30
        risk_factors.append("Negative profit margin")
        suggested_action = "clearance"
    elif margin_data['margin_percentage'] < 5:
        risk_score += 15
        risk_factors.append("Low profit margin")
    
    if holding_cost_ratio > 0.5 and revenue_90d > 0:
        risk_score += 20
        risk_factors.append("High holding cost relative to revenue")
    
    if product.stock_quantity > 0 and days_since_last_sale > 30:
        risk_score += 10
    
    risk_score = min(100.0, risk_score)
    
    # Determine status
    if risk_score >= 70:
        is_dead_stock = "yes"
        if margin_data['margin_percentage'] < 0:
            suggested_action = "clearance"
        elif product.stock_quantity > 0:
            suggested_action = "discount"
        else:
            suggested_action = "stop_ordering"
    elif risk_score >= 40:
        is_dead_stock = "warning"
        suggested_action = "monitor"
    else:
        is_dead_stock = "no"
        suggested_action = "monitor"
    
    # Build explanation
    explanation_parts = []
    if risk_factors:
        explanation_parts.append(f"Risk factors: {', '.join(risk_factors)}.")
    explanation_parts.append(f"Margin: {margin_data['margin_percentage']:.2f}%.")
    explanation_parts.append(f"Current stock: {product.stock_quantity} units.")
    
    if is_dead_stock == "yes":
        explanation_parts.append(f"Suggested action: {suggested_action}.")
    
    explanation = " ".join(explanation_parts)
    
    return {
        'is_dead_stock': is_dead_stock,
        'risk_score': risk_score,
        'demand_trend': trend.value,
        'days_since_last_sale': days_since_last_sale,
        'holding_cost_ratio': float(holding_cost_ratio),
        'margin_status': 'negative' if margin_data['margin_percentage'] < 0 else ('low' if margin_data['margin_percentage'] < 5 else 'healthy'),
        'suggested_action': suggested_action,
        'explanation': explanation
    }
