"""
Vendor Intelligence API
B2B: Internal APIs for vendor ranking, recommendations, and performance tracking
Admin-only endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.models.vendor import Vendor, VendorProduct, VendorPerformanceMetric
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.services.vendor_scoring import update_vendor_scores
from pydantic import BaseModel


def _to_float(v):
    """Safely convert DB numeric (Decimal/None) to float for JSON."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v):
    """Safely convert to int for JSON (e.g. avg_lead_time_days)."""
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


router = APIRouter()


# Request schemas (create)
class VendorCreate(BaseModel):
    name: str
    is_active: bool = True
    avg_lead_time_days: Optional[int] = None
    reliability_score: Optional[float] = None
    cost_score: Optional[float] = None
    overall_score: Optional[float] = None


class VendorProductCreate(BaseModel):
    product_id: int
    unit_cost: float
    min_order_qty: int = 1
    lead_time_days: Optional[int] = None


# Response schemas
class VendorRankingResponse(BaseModel):
    vendor_id: int
    vendor_name: str
    overall_score: Optional[float]
    reliability_score: Optional[float]
    cost_score: Optional[float]
    avg_lead_time_days: Optional[int]
    is_active: bool
    explanation: str  # Why this vendor is ranked here
    
    class Config:
        from_attributes = True


class BestVendorResponse(BaseModel):
    recommended_vendor: VendorRankingResponse
    alternatives: List[VendorRankingResponse]
    reasoning: str  # Explanation of recommendation


class VendorPerformanceResponse(BaseModel):
    vendor_id: int
    vendor_name: str
    metric_date: datetime
    avg_lead_time: Optional[float]
    on_time_delivery_rate: Optional[float]
    fulfillment_rate: Optional[float]
    avg_unit_cost: Optional[float]
    price_variance: Optional[float]
    delay_days_avg: Optional[float]
    
    class Config:
        from_attributes = True


class VendorProductResponse(BaseModel):
    """Product that a vendor supplies (vendor inventory/catalog)"""
    vendor_product_id: int
    product_id: int
    product_name: str
    unit_cost: float
    min_order_qty: int
    lead_time_days: Optional[int]

    class Config:
        from_attributes = True


class VendorCreateResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    avg_lead_time_days: Optional[int]
    reliability_score: Optional[float]
    cost_score: Optional[float]
    overall_score: Optional[float]

    class Config:
        from_attributes = True


@router.post("", response_model=VendorCreateResponse, status_code=201)
def create_vendor(
    body: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new vendor (admin)."""
    existing = db.query(Vendor).filter(Vendor.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vendor with this name already exists")
    vendor = Vendor(
        name=body.name,
        is_active=body.is_active,
        avg_lead_time_days=body.avg_lead_time_days,
        reliability_score=Decimal(str(body.reliability_score)) if body.reliability_score is not None else None,
        cost_score=Decimal(str(body.cost_score)) if body.cost_score is not None else None,
        overall_score=Decimal(str(body.overall_score)) if body.overall_score is not None else None,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return VendorCreateResponse(
        id=vendor.id,
        name=vendor.name,
        is_active=vendor.is_active,
        avg_lead_time_days=vendor.avg_lead_time_days,
        reliability_score=_to_float(vendor.reliability_score),
        cost_score=_to_float(vendor.cost_score),
        overall_score=_to_float(vendor.overall_score),
    )


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Delete a vendor. Fails if the vendor has any purchase orders."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    has_pos = db.query(PurchaseOrder).filter(PurchaseOrder.vendor_id == vendor_id).limit(1).first()
    if has_pos:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete vendor with existing purchase orders. Remove or reassign POs first.",
        )
    db.delete(vendor)
    db.commit()
    return None


@router.get("/rankings", response_model=List[VendorRankingResponse])
def get_vendor_rankings(
    product_id: Optional[int] = Query(None, description="Filter by product"),
    min_reliability: Optional[float] = Query(None, ge=0, le=100, description="Minimum reliability score"),
    max_cost: Optional[float] = Query(None, ge=0, description="Maximum unit cost"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get ranked vendor list.
    
    Sorted by overall_score (descending).
    Supports filtering by product, reliability, and cost.
    """
    query = db.query(Vendor).filter(Vendor.is_active == True)
    
    # Filter by product (vendors that supply this product)
    if product_id:
        vendor_ids = db.query(VendorProduct.vendor_id).filter(
            VendorProduct.product_id == product_id
        ).subquery()
        query = query.filter(Vendor.id.in_(vendor_ids))
    
    # Filter by minimum reliability
    if min_reliability is not None:
        query = query.filter(Vendor.reliability_score >= Decimal(str(min_reliability)))
    
    # Filter by maximum cost (if product_id provided)
    if max_cost is not None and product_id:
        vendor_ids_cheap = db.query(VendorProduct.vendor_id).filter(
            and_(
                VendorProduct.product_id == product_id,
                VendorProduct.unit_cost <= Decimal(str(max_cost))
            )
        ).subquery()
        query = query.filter(Vendor.id.in_(vendor_ids_cheap))
    
    # Sort by overall score (NULLs last)
    vendors = query.order_by(desc(Vendor.overall_score)).all()
    
    results = []
    for idx, vendor in enumerate(vendors):
        # Generate explanation (safe format for Decimal/None)
        explanation_parts = []
        o_score = _to_float(vendor.overall_score)
        r_score = _to_float(vendor.reliability_score)
        c_score = _to_float(vendor.cost_score)
        if o_score is not None:
            explanation_parts.append(f"Overall score: {o_score:.1f}/100")
        if r_score is not None:
            explanation_parts.append(f"Reliability: {r_score:.1f}/100")
        if c_score is not None:
            explanation_parts.append(f"Cost: {c_score:.1f}/100")
        if vendor.avg_lead_time_days is not None:
            explanation_parts.append(f"Avg lead time: {vendor.avg_lead_time_days} days")
        
        explanation = f"Rank #{idx + 1}. " + " | ".join(explanation_parts) if explanation_parts else "No performance data"
        
        results.append(VendorRankingResponse(
            vendor_id=vendor.id,
            vendor_name=str(vendor.name),
            overall_score=o_score,
            reliability_score=r_score,
            cost_score=c_score,
            avg_lead_time_days=_to_int(vendor.avg_lead_time_days),
            is_active=bool(vendor.is_active),
            explanation=explanation
        ))
    
    return results


@router.get("/best-for-product/{product_id}", response_model=BestVendorResponse)
def get_best_vendor_for_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get best vendor recommendation for a product.
    
    Considers:
    - Vendor pricing (vendor_products.unit_cost)
    - Reliability score
    - Lead time
    - Overall score
    
    Returns recommended vendor + 2 alternatives.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get vendors that supply this product
    vendor_products = db.query(VendorProduct).filter(
        VendorProduct.product_id == product_id
    ).join(Vendor).filter(Vendor.is_active == True).all()
    
    if not vendor_products:
        raise HTTPException(status_code=404, detail="No active vendors supply this product")
    
    # Score each vendor-product combination
    scored_vendors = []
    for vp in vendor_products:
        vendor = vp.vendor
        
        # Composite score: overall_score (60%) + cost_factor (40%)
        # Cost factor: lower cost = higher score (normalized)
        if vendor.overall_score:
            base_score = float(vendor.overall_score)
        else:
            base_score = 50.0  # Neutral if no score
        
        # Cost factor: compare to average
        avg_cost = db.query(func.avg(VendorProduct.unit_cost)).filter(
            VendorProduct.product_id == product_id
        ).scalar()
        
        if avg_cost and vp.unit_cost:
            cost_factor = 100.0 - ((float(vp.unit_cost) / float(avg_cost) - 1.0) * 50.0)
            cost_factor = max(0, min(100, cost_factor))
        else:
            cost_factor = 50.0
        
        composite_score = (base_score * 0.6) + (cost_factor * 0.4)
        
        scored_vendors.append({
            "vendor": vendor,
            "vendor_product": vp,
            "composite_score": composite_score
        })
    
    # Sort by composite score
    scored_vendors.sort(key=lambda x: x["composite_score"], reverse=True)
    
    if not scored_vendors:
        raise HTTPException(status_code=404, detail="No vendors available")
    
    # Build response
    recommended = scored_vendors[0]
    alternatives = scored_vendors[1:3]  # Top 2 alternatives
    
    def build_ranking_response(vp_data, rank):
        vendor = vp_data["vendor"]
        vp = vp_data["vendor_product"]
        
        explanation_parts = []
        if vendor.overall_score:
            explanation_parts.append(f"Overall: {vendor.overall_score:.1f}/100")
        explanation_parts.append(f"Unit cost: ${vp.unit_cost:.2f}")
        if vp.lead_time_days:
            explanation_parts.append(f"Lead time: {vp.lead_time_days} days")
        
        return VendorRankingResponse(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            overall_score=float(vendor.overall_score) if vendor.overall_score else None,
            reliability_score=float(vendor.reliability_score) if vendor.reliability_score else None,
            cost_score=float(vendor.cost_score) if vendor.cost_score else None,
            avg_lead_time_days=vendor.avg_lead_time_days,
            is_active=vendor.is_active,
            explanation=f"Rank #{rank}. " + " | ".join(explanation_parts)
        )
    
    # Generate reasoning
    reasoning_parts = [f"Recommended: {recommended['vendor'].name}"]
    if recommended["vendor"].overall_score:
        reasoning_parts.append(f"Overall score: {recommended['vendor'].overall_score:.1f}/100")
    if recommended["vendor_product"].unit_cost:
        reasoning_parts.append(f"Unit cost: ${recommended['vendor_product'].unit_cost:.2f}")
    if recommended["vendor"].reliability_score:
        reasoning_parts.append(f"Reliability: {recommended['vendor'].reliability_score:.1f}/100")
    
    reasoning = ". ".join(reasoning_parts)
    
    return BestVendorResponse(
        recommended_vendor=build_ranking_response(recommended, 1),
        alternatives=[build_ranking_response(alt, idx + 2) for idx, alt in enumerate(alternatives)],
        reasoning=reasoning
    )


@router.get("/{vendor_id}/performance", response_model=List[VendorPerformanceResponse])
def get_vendor_performance(
    vendor_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get vendor performance history (time-series).
    
    Used by dashboards and AI for trend analysis.
    Read-optimized with indexed queries.
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Indexed query for performance
    metrics = db.query(VendorPerformanceMetric).filter(
        and_(
            VendorPerformanceMetric.vendor_id == vendor_id,
            VendorPerformanceMetric.metric_date >= cutoff_date
        )
    ).order_by(VendorPerformanceMetric.metric_date.desc()).all()
    
    results = []
    for metric in metrics:
        results.append(VendorPerformanceResponse(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            metric_date=metric.metric_date,
            avg_lead_time=float(metric.avg_lead_time) if metric.avg_lead_time else None,
            on_time_delivery_rate=float(metric.on_time_delivery_rate) if metric.on_time_delivery_rate else None,
            fulfillment_rate=float(metric.fulfillment_rate) if metric.fulfillment_rate else None,
            avg_unit_cost=float(metric.avg_unit_cost) if metric.avg_unit_cost else None,
            price_variance=float(metric.price_variance) if metric.price_variance else None,
            delay_days_avg=float(metric.delay_days_avg) if metric.delay_days_avg else None
        ))
    
    return results


class VendorComparisonResponse(BaseModel):
    """Dashboard: Vendor comparison for a product"""
    vendor_id: int
    vendor_name: str
    unit_cost: float
    reliability_score: Optional[float]
    lead_time_days: Optional[int]
    risk_score: Optional[float]  # Inverse of reliability
    overall_score: Optional[float]
    
    class Config:
        from_attributes = True


@router.get("/compare-for-product/{product_id}", response_model=List[VendorComparisonResponse])
def compare_vendors_for_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Dashboard: Compare all vendors for a specific product.
    
    Read-optimized: Single query with joins.
    Returns vendors sorted by overall score.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Single optimized query with joins
    vendor_products = db.query(VendorProduct, Vendor).join(
        Vendor, VendorProduct.vendor_id == Vendor.id
    ).filter(
        and_(
            VendorProduct.product_id == product_id,
            Vendor.is_active == True
        )
    ).order_by(desc(Vendor.overall_score)).all()
    
    results = []
    for vp, vendor in vendor_products:
        risk_score = None
        if vendor.reliability_score:
            risk_score = 100.0 - float(vendor.reliability_score)  # Inverse
        
        results.append(VendorComparisonResponse(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            unit_cost=float(vp.unit_cost),
            reliability_score=float(vendor.reliability_score) if vendor.reliability_score else None,
            lead_time_days=vp.lead_time_days or vendor.avg_lead_time_days,
            risk_score=risk_score,
            overall_score=float(vendor.overall_score) if vendor.overall_score else None
        ))
    
    return results


@router.get("/{vendor_id}/products", response_model=List[VendorProductResponse])
def get_vendor_products(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List products (inventory) that a vendor supplies. Use this to place orders."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id, Vendor.is_active == True).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vps = db.query(VendorProduct).filter(VendorProduct.vendor_id == vendor_id).join(Product).all()
    return [
        VendorProductResponse(
            vendor_product_id=vp.id,
            product_id=vp.product_id,
            product_name=getattr(vp.product, "name", None) or f"Product {vp.product_id}",
            unit_cost=_to_float(vp.unit_cost) or 0.0,
            min_order_qty=_to_int(vp.min_order_qty) or 1,
            lead_time_days=_to_int(vp.lead_time_days),
        )
        for vp in vps
    ]


@router.post("/{vendor_id}/products", response_model=VendorProductResponse, status_code=201)
def add_product_to_vendor(
    vendor_id: int,
    body: VendorProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Add a product to a vendor's catalog (admin)."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    product = db.query(Product).filter(Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    existing = db.query(VendorProduct).filter(
        VendorProduct.vendor_id == vendor_id,
        VendorProduct.product_id == body.product_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vendor already supplies this product")
    vp = VendorProduct(
        vendor_id=vendor_id,
        product_id=body.product_id,
        unit_cost=Decimal(str(body.unit_cost)),
        min_order_qty=max(1, body.min_order_qty),
        lead_time_days=body.lead_time_days,
    )
    db.add(vp)
    db.commit()
    db.refresh(vp)
    return VendorProductResponse(
        vendor_product_id=vp.id,
        product_id=vp.product_id,
        product_name=product.name,
        unit_cost=_to_float(vp.unit_cost) or 0.0,
        min_order_qty=_to_int(vp.min_order_qty) or 1,
        lead_time_days=_to_int(vp.lead_time_days),
    )


class VendorScorecardResponse(BaseModel):
    """Dashboard: Vendor scorecard with trends"""
    vendor_id: int
    vendor_name: str
    current_reliability: Optional[float]
    reliability_trend: str  # "rising", "stable", "declining"
    current_cost_score: Optional[float]
    cost_volatility: Optional[float]  # price_variance
    delay_trend: Optional[float]  # Recent delay_days_avg
    overall_score: Optional[float]
    action_insights: List[str]  # Human-readable insights
    
    class Config:
        from_attributes = True


@router.get("/{vendor_id}/scorecard", response_model=VendorScorecardResponse)
def get_vendor_scorecard(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Dashboard: Vendor scorecard with trends and action insights.
    
    Read-optimized: Aggregated queries.
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Get recent metrics (last 2 periods for trend)
    metrics = db.query(VendorPerformanceMetric).filter(
        VendorPerformanceMetric.vendor_id == vendor_id
    ).order_by(desc(VendorPerformanceMetric.metric_date)).limit(2).all()
    
    current_reliability = float(vendor.reliability_score) if vendor.reliability_score else None
    reliability_trend = "stable"
    
    if len(metrics) >= 2:
        recent_otd = metrics[0].on_time_delivery_rate
        previous_otd = metrics[1].on_time_delivery_rate
        if recent_otd and previous_otd:
            if recent_otd > previous_otd + 5:
                reliability_trend = "rising"
            elif recent_otd < previous_otd - 5:
                reliability_trend = "declining"
    
    # Cost volatility (latest price_variance)
    cost_volatility = float(metrics[0].price_variance) if metrics and metrics[0].price_variance else None
    
    # Delay trend
    delay_trend = float(metrics[0].delay_days_avg) if metrics and metrics[0].delay_days_avg else None
    
    # Generate action insights
    insights = []
    if vendor.overall_score:
        if vendor.overall_score < 50:
            insights.append("⚠️ Avoid vendor this week - Low overall score")
        elif vendor.reliability_score and vendor.reliability_score < 60:
            insights.append("⚠️ High delay risk - Consider alternatives")
        elif vendor.cost_score and vendor.cost_score < 50:
            insights.append("💰 Reliable but expensive - Premium pricing")
        elif vendor.overall_score > 80:
            insights.append("✅ Top performer - Recommended vendor")
    
    if delay_trend and delay_trend > 5:
        insights.append("🚨 High average delays - Monitor closely")
    
    if cost_volatility and cost_volatility > 10:
        insights.append("📊 High price volatility - Inconsistent pricing")
    
    return VendorScorecardResponse(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        current_reliability=current_reliability,
        reliability_trend=reliability_trend,
        current_cost_score=float(vendor.cost_score) if vendor.cost_score else None,
        cost_volatility=cost_volatility,
        delay_trend=delay_trend,
        overall_score=float(vendor.overall_score) if vendor.overall_score else None,
        action_insights=insights if insights else ["✅ No issues detected"]
    )
