"""
Vendor Scoring Logic
B2B: Deterministic scoring system for vendor intelligence

Scoring Formulas (all scores 0-100, higher is better):

Reliability Score:
- Based on: on_time_delivery_rate, fulfillment_rate, avg_delay_days
- Formula: (on_time_delivery_rate * 0.5) + (fulfillment_rate * 0.3) + ((100 - min(avg_delay_days * 10, 100)) * 0.2)
- Higher delay = lower score (penalty)

Cost Score:
- Based on: avg_unit_cost (relative to market), price_variance (penalty)
- Formula: Normalized cost score (lower cost = higher score)
- Price variance penalizes inconsistent pricing

Overall Score:
- Weighted average: (reliability_score * 0.6) + (cost_score * 0.4)
- Configurable weights via constants
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from decimal import Decimal
from typing import Optional
from app.models.vendor import Vendor, VendorProduct, VendorPerformanceMetric
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
import logging

logger = logging.getLogger(__name__)

# Scoring weights (configurable)
RELIABILITY_WEIGHT = Decimal("0.6")
COST_WEIGHT = Decimal("0.4")

# Reliability sub-weights
ON_TIME_DELIVERY_WEIGHT = Decimal("0.5")
FULFILLMENT_RATE_WEIGHT = Decimal("0.3")
DELAY_PENALTY_WEIGHT = Decimal("0.2")

# Delay penalty: each day of delay reduces score by 10 points (max 100)
DELAY_PENALTY_PER_DAY = Decimal("10")


def calculate_reliability_score(
    on_time_delivery_rate: Optional[Decimal],
    fulfillment_rate: Optional[Decimal],
    avg_delay_days: Optional[Decimal]
) -> Optional[Decimal]:
    """
    Calculate reliability score (0-100)
    
    Formula:
    - on_time_delivery_rate * 0.5
    - fulfillment_rate * 0.3
    - delay_penalty * 0.2 (inverse: lower delay = higher score)
    
    Returns None if insufficient data.
    """
    if on_time_delivery_rate is None or fulfillment_rate is None:
        return None
    
    # Delay penalty: convert delay days to score (0-100)
    # Each day of delay reduces score by 10 points, max 100
    delay_score = Decimal("100")
    if avg_delay_days is not None and avg_delay_days > 0:
        delay_penalty = min(avg_delay_days * DELAY_PENALTY_PER_DAY, Decimal("100"))
        delay_score = max(Decimal("0"), Decimal("100") - delay_penalty)
    
    # Weighted average
    reliability = (
        (on_time_delivery_rate * ON_TIME_DELIVERY_WEIGHT) +
        (fulfillment_rate * FULFILLMENT_RATE_WEIGHT) +
        (delay_score * DELAY_PENALTY_WEIGHT)
    )
    
    return max(Decimal("0"), min(Decimal("100"), reliability))


def calculate_cost_score(
    vendor_avg_cost: Decimal,
    market_avg_cost: Decimal,
    price_variance: Optional[Decimal]
) -> Decimal:
    """
    Calculate cost score (0-100)
    
    Formula:
    - Lower cost relative to market = higher score
    - Price variance penalizes inconsistent pricing
    
    Returns 0-100 score.
    """
    if market_avg_cost == 0:
        return Decimal("50")  # Neutral if no market data
    
    # Cost ratio: vendor_cost / market_cost
    # Lower ratio = better (cheaper)
    cost_ratio = vendor_avg_cost / market_avg_cost
    
    # Convert ratio to score: 1.0 = 50 points, 0.8 = 80 points, 1.2 = 20 points
    # Linear mapping: score = 100 - (ratio - 0.5) * 100
    base_score = Decimal("100") - ((cost_ratio - Decimal("0.5")) * Decimal("100"))
    base_score = max(Decimal("0"), min(Decimal("100"), base_score))
    
    # Apply variance penalty (higher variance = lower score)
    variance_penalty = Decimal("0")
    if price_variance is not None and price_variance > 0:
        # Penalty: up to 20 points for high variance
        variance_penalty = min(price_variance / vendor_avg_cost * Decimal("20"), Decimal("20"))
    
    final_score = max(Decimal("0"), base_score - variance_penalty)
    return final_score


def calculate_overall_score(
    reliability_score: Optional[Decimal],
    cost_score: Optional[Decimal]
) -> Optional[Decimal]:
    """
    Calculate overall vendor score (0-100)
    
    Formula:
    - reliability_score * 0.6 + cost_score * 0.4
    
    Returns None if either score is missing.
    """
    if reliability_score is None or cost_score is None:
        return None
    
    overall = (
        (reliability_score * RELIABILITY_WEIGHT) +
        (cost_score * COST_WEIGHT)
    )
    
    return max(Decimal("0"), min(Decimal("100"), overall))


def update_vendor_scores(db: Session, vendor_id: int) -> Optional[Vendor]:
    """
    Update all scores for a vendor based on performance metrics.
    
    Uses latest vendor_performance_metrics record.
    Computes market average from all vendors for cost comparison.
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        return None
    
    # Get latest performance metrics
    latest_metric = db.query(VendorPerformanceMetric).filter(
        VendorPerformanceMetric.vendor_id == vendor_id
    ).order_by(VendorPerformanceMetric.metric_date.desc()).first()
    
    if not latest_metric:
        logger.warning(f"No performance metrics found for vendor {vendor_id}")
        return vendor
    
    # Calculate reliability score
    reliability_score = calculate_reliability_score(
        latest_metric.on_time_delivery_rate,
        latest_metric.fulfillment_rate,
        latest_metric.delay_days_avg
    )
    
    # Calculate cost score (need market average)
    if latest_metric.avg_unit_cost:
        # Get market average cost for products this vendor supplies
        vendor_products = db.query(VendorProduct).filter(
            VendorProduct.vendor_id == vendor_id
        ).all()
        
        if vendor_products:
            product_ids = [vp.product_id for vp in vendor_products]
            market_avg = db.query(func.avg(VendorProduct.unit_cost)).filter(
                VendorProduct.product_id.in_(product_ids)
            ).scalar()
            
            market_avg_cost = Decimal(str(market_avg)) if market_avg else latest_metric.avg_unit_cost
        else:
            market_avg_cost = latest_metric.avg_unit_cost
        
        cost_score = calculate_cost_score(
            latest_metric.avg_unit_cost,
            market_avg_cost,
            latest_metric.price_variance
        )
    else:
        cost_score = None
    
    # Calculate overall score
    overall_score = calculate_overall_score(reliability_score, cost_score)
    
    # Update vendor record
    vendor.reliability_score = reliability_score
    vendor.cost_score = cost_score
    vendor.overall_score = overall_score
    vendor.avg_lead_time_days = int(latest_metric.avg_lead_time) if latest_metric.avg_lead_time else None
    
    db.commit()
    db.refresh(vendor)
    
    logger.info(f"Updated scores for vendor {vendor_id}: reliability={reliability_score}, cost={cost_score}, overall={overall_score}")
    
    return vendor


def compute_vendor_metrics(db: Session, vendor_id: int, metric_date=None) -> VendorPerformanceMetric:
    """
    Compute vendor performance metrics from purchase order history.
    
    Calculates:
    - avg_lead_time
    - on_time_delivery_rate
    - fulfillment_rate
    - avg_unit_cost
    - price_variance
    - delay_days_avg
    """
    from datetime import datetime
    
    if metric_date is None:
        metric_date = datetime.now()
    
    # Get delivered purchase orders
    delivered_pos = db.query(PurchaseOrder).filter(
        and_(
            PurchaseOrder.vendor_id == vendor_id,
            PurchaseOrder.status == PurchaseOrderStatus.DELIVERED.value
        )
    ).all()
    
    if not delivered_pos:
        # Return empty metrics if no history
        metric = VendorPerformanceMetric(
            vendor_id=vendor_id,
            metric_date=metric_date,
            avg_lead_time=None,
            on_time_delivery_rate=None,
            fulfillment_rate=None,
            avg_unit_cost=None,
            price_variance=None,
            delay_days_avg=None
        )
        db.add(metric)
        db.commit()
        return metric
    
    # Calculate metrics
    total_orders = len(delivered_pos)
    on_time_count = sum(1 for po in delivered_pos if po.delay_days is not None and po.delay_days <= 0)
    on_time_delivery_rate = Decimal(str((on_time_count / total_orders) * 100)) if total_orders > 0 else None
    
    # Fulfillment rate (orders delivered / orders created)
    total_created = db.query(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == vendor_id
    ).count()
    fulfillment_rate = Decimal(str((total_orders / total_created) * 100)) if total_created > 0 else None
    
    # Average lead time
    lead_times = []
    for po in delivered_pos:
        if po.promised_delivery_date and po.order_date:
            lead_time = (po.promised_delivery_date - po.order_date).days
            lead_times.append(lead_time)
    avg_lead_time = Decimal(str(sum(lead_times) / len(lead_times))) if lead_times else None
    
    # Average delay (only for late deliveries)
    delays = [po.delay_days for po in delivered_pos if po.delay_days is not None and po.delay_days > 0]
    delay_days_avg = Decimal(str(sum(delays) / len(delays))) if delays else Decimal("0")
    
    # Average unit cost and variance from purchase order items
    from app.models.purchase_order import PurchaseOrderItem
    all_items = db.query(PurchaseOrderItem).join(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == vendor_id,
        PurchaseOrder.status == PurchaseOrderStatus.DELIVERED.value
    ).all()
    
    if all_items:
        costs = [float(item.unit_cost) for item in all_items]
        import statistics
        avg_unit_cost = Decimal(str(statistics.mean(costs)))
        price_variance = Decimal(str(statistics.stdev(costs))) if len(costs) > 1 else Decimal("0")
    else:
        avg_unit_cost = None
        price_variance = None
    
    # Create or update metric
    metric = VendorPerformanceMetric(
        vendor_id=vendor_id,
        metric_date=metric_date,
        avg_lead_time=avg_lead_time,
        on_time_delivery_rate=on_time_delivery_rate,
        fulfillment_rate=fulfillment_rate,
        avg_unit_cost=avg_unit_cost,
        price_variance=price_variance,
        delay_days_avg=delay_days_avg
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    
    return metric
