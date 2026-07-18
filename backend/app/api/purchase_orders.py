"""
Purchase Orders API
B2B: Create and list purchase orders (place orders from vendors).
Admin-only.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.core.exceptions import ValidationError
from app.models.user import User
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus
from app.models.vendor import Vendor
from app.models.product import Product
from app.services.vendor_service import create_purchase_order

router = APIRouter()


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_cost: float


class PurchaseOrderCreate(BaseModel):
    vendor_id: int
    items: List[PurchaseOrderItemCreate]
    promised_delivery_date: Optional[datetime] = None


class PurchaseOrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_cost: float
    total_cost: float

    class Config:
        from_attributes = True


class PurchaseOrderResponse(BaseModel):
    id: int
    vendor_id: int
    vendor_name: str
    po_number: str
    status: str
    total_cost: float
    order_date: datetime
    promised_delivery_date: Optional[datetime]
    actual_delivery_date: Optional[datetime]
    items: List[PurchaseOrderItemResponse]

    class Config:
        from_attributes = True


@router.post("", response_model=PurchaseOrderResponse)
def create_po(
    body: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Place an order with a vendor. Items must be products the vendor supplies; quantity >= min_order_qty per product."""
    if not body.items:
        raise HTTPException(status_code=400, detail="At least one item is required")
    items_dict = [
        {"product_id": i.product_id, "quantity": i.quantity, "unit_cost": i.unit_cost}
        for i in body.items
    ]
    try:
        po = create_purchase_order(
            db,
            vendor_id=body.vendor_id,
            items=items_dict,
            promised_delivery_date=body.promised_delivery_date,
        )
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    po_with_relations = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.vendor),
        joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
    ).filter(PurchaseOrder.id == po.id).first()
    items = po_with_relations.items if po_with_relations else []
    return PurchaseOrderResponse(
        id=po.id,
        vendor_id=po.vendor_id,
        vendor_name=po_with_relations.vendor.name if po_with_relations and po_with_relations.vendor else "",
        po_number=po.po_number,
        status=po.status,
        total_cost=float(po.total_cost),
        order_date=po.order_date,
        promised_delivery_date=po.promised_delivery_date,
        actual_delivery_date=po.actual_delivery_date,
        items=[
            PurchaseOrderItemResponse(
                product_id=item.product_id,
                product_name=item.product.name if item.product else f"Product #{item.product_id}",
                quantity=item.quantity,
                unit_cost=float(item.unit_cost),
                total_cost=float(item.total_cost),
            )
            for item in items
        ],
    )


@router.get("", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List purchase orders, optionally filtered by vendor."""
    query = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.vendor),
            joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.product),
        )
        .order_by(PurchaseOrder.order_date.desc())
    )
    if vendor_id is not None:
        query = query.filter(PurchaseOrder.vendor_id == vendor_id)
    orders = query.limit(100).all()
    result = []
    for po in orders:
        result.append(
            PurchaseOrderResponse(
                id=po.id,
                vendor_id=po.vendor_id,
                vendor_name=po.vendor.name if po.vendor else "",
                po_number=po.po_number,
                status=po.status,
                total_cost=float(po.total_cost),
                order_date=po.order_date,
                promised_delivery_date=po.promised_delivery_date,
                actual_delivery_date=po.actual_delivery_date,
                items=[
                    PurchaseOrderItemResponse(
                        product_id=item.product_id,
                        product_name=item.product.name if item.product else f"Product #{item.product_id}",
                        quantity=item.quantity,
                        unit_cost=float(item.unit_cost),
                        total_cost=float(item.total_cost),
                    )
                    for item in po.items
                ],
            )
        )
    return result
