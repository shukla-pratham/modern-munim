"""Purchase-order delivery updates stock once and does not duplicate the ledger."""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.main import app  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem  # noqa: E402
from app.models.stock_transaction import StockTransaction  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.vendor import Vendor, VendorProduct  # noqa: E402
from app.services.auth_service import create_user_token  # noqa: E402


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, base_url="http://localhost")


@pytest.fixture
def admin_headers(db: Session):
    email = f"po_deliver_{uuid.uuid4().hex[:12]}@example.com"
    user = User(
        email=email,
        password_hash=get_password_hash("test-pass-1234"),
        role=UserRole.ADMIN,
        store_name="PO delivery test",
        store_type="Grocery",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    headers = {"Authorization": f"Bearer {create_user_token(user)}"}
    yield headers, user.id
    db.query(User).filter(User.id == user.id).delete()
    db.commit()


def _cleanup(db: Session, product_id: int, vendor_id: int, po_id: int | None) -> None:
    if po_id is not None:
        db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == po_id).delete()
        db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).delete()
    db.query(StockTransaction).filter(StockTransaction.product_id == product_id).delete()
    db.query(VendorProduct).filter(VendorProduct.vendor_id == vendor_id).delete()
    db.query(Vendor).filter(Vendor.id == vendor_id).delete()
    db.query(Product).filter(Product.id == product_id).delete()
    db.commit()


def test_deliver_purchase_order_once_updates_stock_and_ledger(client: TestClient, db: Session, admin_headers):
    headers, _user_id = admin_headers
    marker = f"po-deliver-{uuid.uuid4().hex[:8]}"
    product = client.post(
        "/api/products",
        headers=headers,
        json={
            "name": marker,
            "description": "delivery regression",
            "price": "10.00",
            "stock_quantity": 2,
            "stock_threshold": 1,
        },
    )
    assert product.status_code == 201, product.text
    product_id = product.json()["id"]
    assert product.json()["stock_quantity"] == 2

    vendor = client.post(
        "/api/vendors",
        headers=headers,
        json={"name": f"vendor-{marker}", "is_active": True},
    )
    assert vendor.status_code == 201, vendor.text
    vendor_id = vendor.json()["id"]
    link = client.post(
        f"/api/vendors/{vendor_id}/products",
        headers=headers,
        json={"product_id": product_id, "unit_cost": 4.5, "min_order_qty": 1},
    )
    assert link.status_code == 201, link.text

    po_id = None
    try:
        created = client.post(
            "/api/purchase-orders",
            headers=headers,
            json={
                "vendor_id": vendor_id,
                "items": [{"product_id": product_id, "quantity": 3, "unit_cost": 4.5}],
            },
        )
        assert created.status_code == 200, created.text
        body = created.json()
        po_id = body["id"]
        assert body["status"] == "created"
        assert body["items"][0]["quantity"] == 3
        db.expire_all()
        assert db.get(Product, product_id).stock_quantity == 2
        assert db.query(StockTransaction).filter(StockTransaction.product_id == product_id).count() == 0

        first = client.post(f"/api/purchase-orders/{po_id}/deliver", headers=headers)
        assert first.status_code == 200, first.text
        assert first.json()["status"] == "delivered"
        db.expire_all()
        assert db.get(Product, product_id).stock_quantity == 5
        rows = db.query(StockTransaction).filter(StockTransaction.product_id == product_id).all()
        assert len(rows) == 1
        assert rows[0].quantity_change == 3
        assert rows[0].transaction_type.value == "in"
        assert body["po_number"] in (rows[0].reason or "")

        second = client.post(f"/api/purchase-orders/{po_id}/deliver", headers=headers)
        assert second.status_code == 200, second.text
        assert second.json()["status"] == "delivered"
        db.expire_all()
        assert db.get(Product, product_id).stock_quantity == 5
        assert db.query(StockTransaction).filter(StockTransaction.product_id == product_id).count() == 1

        missing = client.post("/api/purchase-orders/999999/deliver", headers=headers)
        assert missing.status_code == 404
        bad = client.post(
            f"/api/purchase-orders/{po_id}/deliver?actual_delivery_date=not-a-date",
            headers=headers,
        )
        assert bad.status_code == 422
        db.expire_all()
        assert db.get(Product, product_id).stock_quantity == 5
        assert db.query(StockTransaction).filter(StockTransaction.product_id == product_id).count() == 1
    finally:
        _cleanup(db, product_id, vendor_id, po_id)
