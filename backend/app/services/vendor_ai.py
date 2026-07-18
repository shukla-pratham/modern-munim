"""
Vendor AI Intelligence
B2B: Statistical/rule-based ML for vendor delay prediction and auto-switch recommendations

NO external ML APIs - uses statistical methods only.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from decimal import Decimal
from app.models.vendor import Vendor, VendorProduct, VendorPerformanceMetric
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.ai_forecast import AIAlert
from app.models.product import Product
from app.services.vendor_scoring import compute_vendor_metrics, update_vendor_scores
import logging
import statistics

logger = logging.getLogger(__name__)


def predict_vendor_delay_probability(
    db: Session,
    vendor_id: int,
    promised_delivery_date: datetime
) -> Dict:
    """
    Predict probability of late delivery for a vendor.
    
    Statistical method:
    - Analyze historical delay patterns
    - Consider recent trend (last 30 days)
    - Factor in order volume
    
    Returns:
    {
        'delay_probability': 0.0-1.0,
        'expected_delay_days': float,
        'confidence': 0.0-1.0,
        'explanation': str
    }
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        return None
    
    # Get recent purchase orders (last 90 days)
    cutoff_date = datetime.now() - timedelta(days=90)
    recent_pos = db.query(PurchaseOrder).filter(
        and_(
            PurchaseOrder.vendor_id == vendor_id,
            PurchaseOrder.status == PurchaseOrderStatus.DELIVERED.value,
            PurchaseOrder.order_date >= cutoff_date
        )
    ).all()
    
    if len(recent_pos) < 3:
        # Insufficient data
        return {
            'delay_probability': 0.5,  # Neutral
            'expected_delay_days': 0.0,
            'confidence': 0.3,
            'explanation': f"Insufficient delivery history ({len(recent_pos)} orders). Cannot reliably predict delays."
        }
    
    # Calculate delay statistics
    delays = [po.delay_days for po in recent_pos if po.delay_days is not None and po.delay_days > 0]
    late_count = len(delays)
    total_count = len(recent_pos)
    
    # Delay probability = proportion of late deliveries
    delay_probability = late_count / total_count if total_count > 0 else 0.0
    
    # Expected delay (average of late deliveries)
    expected_delay_days = statistics.mean(delays) if delays else 0.0
    
    # Confidence based on sample size
    confidence = min(1.0, total_count / 20.0)  # Max confidence at 20+ orders
    
    # Recent trend (last 30 days)
    recent_cutoff = datetime.now() - timedelta(days=30)
    recent_pos_30 = [po for po in recent_pos if po.order_date >= recent_cutoff]
    recent_late_count = sum(1 for po in recent_pos_30 if po.delay_days and po.delay_days > 0)
    recent_delay_rate = recent_late_count / len(recent_pos_30) if recent_pos_30 else delay_probability
    
    # Adjust probability based on recent trend
    if recent_delay_rate > delay_probability:
        # Getting worse
        delay_probability = min(1.0, delay_probability * 1.2)
        trend_note = "worsening"
    elif recent_delay_rate < delay_probability:
        # Getting better
        delay_probability = max(0.0, delay_probability * 0.8)
        trend_note = "improving"
    else:
        trend_note = "stable"
    
    explanation = (
        f"Based on {total_count} recent deliveries: {late_count} late ({delay_probability*100:.1f}% rate). "
        f"Average delay when late: {expected_delay_days:.1f} days. "
        f"Recent trend: {trend_note}."
    )
    
    return {
        'delay_probability': float(delay_probability),
        'expected_delay_days': float(expected_delay_days),
        'confidence': float(confidence),
        'explanation': explanation
    }


def recommend_vendor_switch(
    db: Session,
    product_id: int,
    current_vendor_id: int
) -> Optional[Dict]:
    """
    Detect if vendor switch is recommended for a product.
    
    Triggers:
    - High delay risk (>50% probability)
    - Reliability score drop (>20 points in 30 days)
    - Consistent late deliveries
    
    Returns recommendation with alternative vendors.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    current_vendor = db.query(Vendor).filter(Vendor.id == current_vendor_id).first()
    if not current_vendor or not current_vendor.is_active:
        return None
    
    # Check delay risk for upcoming orders
    # Get pending purchase orders for this vendor-product
    pending_pos = db.query(PurchaseOrder).join(PurchaseOrderItem).filter(
        and_(
            PurchaseOrder.vendor_id == current_vendor_id,
            PurchaseOrder.status.in_([PurchaseOrderStatus.CREATED.value, PurchaseOrderStatus.ORDERED.value]),
            PurchaseOrderItem.product_id == product_id
        )
    ).all()
    
    high_risk = False
    risk_reasons = []
    
    # Check delay probability for pending orders
    for po in pending_pos:
        if po.promised_delivery_date:
            prediction = predict_vendor_delay_probability(db, current_vendor_id, po.promised_delivery_date)
            if prediction and prediction['delay_probability'] > 0.5:
                high_risk = True
                risk_reasons.append(f"Pending PO {po.po_number}: {prediction['delay_probability']*100:.0f}% delay risk")
    
    # Check reliability score trend
    metrics = db.query(VendorPerformanceMetric).filter(
        VendorPerformanceMetric.vendor_id == current_vendor_id
    ).order_by(VendorPerformanceMetric.metric_date.desc()).limit(2).all()
    
    if len(metrics) >= 2:
        recent_score = metrics[0].on_time_delivery_rate
        previous_score = metrics[1].on_time_delivery_rate
        if recent_score and previous_score and (previous_score - recent_score) > 20:
            high_risk = True
            risk_reasons.append(f"Reliability dropped {previous_score - recent_score:.1f} points")
    
    if not high_risk:
        return None  # No switch needed
    
    # Find alternative vendors for this product
    alternatives = db.query(VendorProduct).join(Vendor).filter(
        and_(
            VendorProduct.product_id == product_id,
            Vendor.id != current_vendor_id,
            Vendor.is_active == True
        )
    ).order_by(desc(Vendor.overall_score)).limit(3).all()
    
    if not alternatives:
        return None  # No alternatives available
    
    # Build recommendation
    recommended_vendor = alternatives[0].vendor
    alternative_vendors = [alt.vendor for alt in alternatives[1:]]
    
    explanation = (
        f"Current vendor '{current_vendor.name}' shows high risk: " + "; ".join(risk_reasons) + ". "
        f"Recommended switch to '{recommended_vendor.name}' "
        f"(overall score: {recommended_vendor.overall_score:.1f}/100)."
    )
    
    return {
        'product_id': product_id,
        'product_name': product.name,
        'current_vendor_id': current_vendor_id,
        'current_vendor_name': current_vendor.name,
        'recommended_vendor_id': recommended_vendor.id,
        'recommended_vendor_name': recommended_vendor.name,
        'alternative_vendor_ids': [v.id for v in alternative_vendors],
        'risk_reasons': risk_reasons,
        'explanation': explanation
    }


def process_vendor_intelligence_batch(db: Session) -> Dict:
    """
    Batch process vendor intelligence:
    1. Compute performance metrics for all vendors
    2. Update vendor scores
    3. Predict delays for pending orders
    4. Generate switch recommendations
    5. Create AI alerts
    
    Returns summary of processing.
    """
    summary = {
        'vendors_processed': 0,
        'metrics_computed': 0,
        'scores_updated': 0,
        'delay_predictions': 0,
        'switch_recommendations': 0,
        'alerts_created': 0,
        'errors': []
    }
    
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    
    logger.info(f"Processing vendor intelligence for {len(vendors)} vendors")
    
    for vendor in vendors:
        try:
            # Compute performance metrics
            metric = compute_vendor_metrics(db, vendor.id)
            if metric:
                summary['metrics_computed'] += 1
            
            # Update scores
            updated_vendor = update_vendor_scores(db, vendor.id)
            if updated_vendor:
                summary['scores_updated'] += 1
            
            summary['vendors_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing vendor {vendor.id}: {e}", exc_info=True)
            summary['errors'].append({
                'vendor_id': vendor.id,
                'operation': 'metrics_computation',
                'error': str(e)
            })
            db.rollback()
    
    # Process switch recommendations for products with multiple vendors
    products_with_vendors = db.query(Product.id).join(VendorProduct).group_by(Product.id).having(
        func.count(VendorProduct.vendor_id) > 1
    ).all()
    
    for (product_id,) in products_with_vendors:
        try:
            # Get current primary vendor (highest overall score)
            vendor_products = db.query(VendorProduct).filter(
                VendorProduct.product_id == product_id
            ).join(Vendor).filter(Vendor.is_active == True).all()
            
            if len(vendor_products) < 2:
                continue  # Need at least 2 vendors for switch
            
            # Find vendor with most recent orders (current vendor)
            current_vendor_id = None
            recent_po = db.query(PurchaseOrder).join(PurchaseOrderItem).filter(
                PurchaseOrderItem.product_id == product_id
            ).order_by(desc(PurchaseOrder.order_date)).first()
            
            if recent_po:
                current_vendor_id = recent_po.vendor_id
            
            if not current_vendor_id:
                continue  # No order history
            
            # Check if switch is recommended
            recommendation = recommend_vendor_switch(db, product_id, current_vendor_id)
            
            if recommendation:
                summary['switch_recommendations'] += 1
                
                # Create AI alert
                product = db.query(Product).filter(Product.id == product_id).first()
                alert = AIAlert(
                    product_id=product_id,
                    alert_type='vendor_switch_recommended',
                    severity='medium',
                    message=recommendation['explanation'],
                    is_resolved=False
                )
                db.add(alert)
                summary['alerts_created'] += 1
        
        except Exception as e:
            logger.error(f"Error processing switch recommendation for product {product_id}: {e}")
            summary['errors'].append({
                'product_id': product_id,
                'operation': 'switch_recommendation',
                'error': str(e)
            })
            db.rollback()
    
    db.commit()
    
    logger.info(f"Vendor intelligence batch processing completed: {summary}")
    return summary
