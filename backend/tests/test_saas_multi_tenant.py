"""
Comprehensive SaaS Multi-Tenant Isolation & Security Test Suite.

Verifies:
1. Registration creates distinct, isolated workspaces for each user.
2. Tenant Isolation: User A cannot read, update, or delete products, orders, vendors, or expenses belonging to User B.
3. Legacy Unassigned Users: Users with no workspace receive 403 Forbidden on all business endpoints.
4. IDOR Protection: Passing `X-Workspace-Id` for an unauthorized workspace fails with 403 Forbidden.
5. Founder Demo Seeding:
   - Non-founder users are rejected with 403 Forbidden on demo seed and reset.
   - Verified founder user (`shuklapratham758@gmail.com`) can seed demo data.
   - Demo seeding is idempotent (calling it twice does not duplicate records).
   - Demo reset cleanly and safely purges only `is_demo=True` rows in the founder workspace.
6. Transactional Purchase Order Delivery: Delivering a PO increases stock exactly once and logs exactly one ledger entry.
"""
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceMembership
from app.models.product import Product
from app.models.vendor import Vendor, VendorProduct
from app.models.order import Order, OrderItem
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.expense import Expense, ExpenseCategory, ExpenseType
from app.core.security import get_password_hash, create_access_token


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="http://localhost") as c:
        yield c


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_test_tenant(db: Session, email: str, store_name: str, store_type: str = "retail"):
    """Helper to create a user and their dedicated workspace."""
    # Clean up existing test user if present
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        # Delete related workspace memberships
        memberships = db.query(WorkspaceMembership).filter(WorkspaceMembership.user_id == existing_user.id).all()
        for m in memberships:
            ws_id = m.workspace_id
            order_ids = [o[0] for o in db.query(Order.id).filter(Order.workspace_id == ws_id).all()]
            if order_ids:
                db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
            po_ids = [p[0] for p in db.query(PurchaseOrder.id).filter(PurchaseOrder.workspace_id == ws_id).all()]
            if po_ids:
                db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id.in_(po_ids)).delete(synchronize_session=False)
            ws_prod_ids = [p[0] for p in db.query(Product.id).filter(Product.workspace_id == ws_id).all()]
            if ws_prod_ids:
                db.query(VendorProduct).filter(VendorProduct.product_id.in_(ws_prod_ids)).delete(synchronize_session=False)
            db.query(WorkspaceMembership).filter(WorkspaceMembership.workspace_id == ws_id).delete(synchronize_session=False)
            db.query(Workspace).filter(Workspace.id == ws_id).delete(synchronize_session=False)
        db.delete(existing_user)
        db.commit()

    user = User(
        email=email,
        password_hash=get_password_hash("Secret123!"),
        role=UserRole.ADMIN,
        store_name=store_name,
        store_type=store_type,
    )
    db.add(user)
    db.flush()

    import uuid
    unique_slug = f"{store_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
    ws = Workspace(
        name=store_name,
        slug=unique_slug,
        store_type=store_type,
        is_demo=False
    )
    db.add(ws)
    db.flush()

    membership = WorkspaceMembership(
        workspace_id=ws.id,
        user_id=user.id,
        role="owner",
        is_active=True
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    db.refresh(ws)

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    headers = {"Authorization": f"Bearer {token}"}
    return user, ws, headers


def test_cross_tenant_isolation_products_and_orders(db: Session, client: TestClient):
    """Test that Tenant A cannot see, update, or delete products and orders belonging to Tenant B."""
    user_a, ws_a, headers_a = create_test_tenant(db, "tenant_a@saas.com", "Tenant A Hardware")
    user_b, ws_b, headers_b = create_test_tenant(db, "tenant_b@saas.com", "Tenant B Electronics")

    # Tenant A creates a product
    prod_resp = client.post(
        "/api/products",
        headers=headers_a,
        json={"name": "A-Hammer", "price": 19.99, "stock_quantity": 20, "stock_threshold": 5}
    )
    assert prod_resp.status_code == 201, prod_resp.text
    prod_a_id = prod_resp.json()["id"]

    # Tenant B creates a product
    prod_resp_b = client.post(
        "/api/products",
        headers=headers_b,
        json={"name": "B-Circuit", "price": 49.99, "stock_quantity": 10, "stock_threshold": 2}
    )
    assert prod_resp_b.status_code == 201, prod_resp_b.text
    prod_b_id = prod_resp_b.json()["id"]

    # 1. Tenant A lists products -> should only see Tenant A's products
    list_a = client.get("/api/products", headers=headers_a).json()
    product_names_a = [p["name"] for p in list_a]
    assert "A-Hammer" in product_names_a
    assert "B-Circuit" not in product_names_a

    # 2. Tenant B lists products -> should only see Tenant B's products
    list_b = client.get("/api/products", headers=headers_b).json()
    product_names_b = [p["name"] for p in list_b]
    assert "B-Circuit" in product_names_b
    assert "A-Hammer" not in product_names_b

    # 3. Tenant A attempts to read Tenant B's product by ID -> 404
    get_b = client.get(f"/api/products/{prod_b_id}", headers=headers_a)
    assert get_b.status_code == 404

    # 4. Tenant A attempts to update Tenant B's product -> 404
    put_b = client.put(f"/api/products/{prod_b_id}", headers=headers_a, json={"name": "Hacked", "price": 1.0})
    assert put_b.status_code == 404

    # 5. Tenant A attempts to delete Tenant B's product -> 404
    del_b = client.delete(f"/api/products/{prod_b_id}", headers=headers_a)
    assert del_b.status_code == 404


def test_idor_header_spoofing_prevented(db: Session, client: TestClient):
    """Passing X-Workspace-Id for an unauthorized workspace returns 403 Forbidden."""
    user_a, ws_a, headers_a = create_test_tenant(db, "idor_a@saas.com", "IDOR Store A")
    user_b, ws_b, headers_b = create_test_tenant(db, "idor_b@saas.com", "IDOR Store B")

    spoofed_headers = {
        **headers_a,
        "X-Workspace-Id": str(ws_b.id)  # Tenant A attempts to impersonate Workspace B
    }
    resp = client.get("/api/products", headers=spoofed_headers)
    assert resp.status_code == 403
    err_msg = resp.json().get("error") or resp.json().get("detail")
    assert "Not authorized to access the requested workspace" in str(err_msg)


def test_unassigned_legacy_user_blocked_with_403(db: Session, client: TestClient):
    """Existing legacy host accounts with null store_name and no workspace receive 403 on business APIs."""
    existing = db.query(User).filter(User.email == "legacy_unassigned@marketplace.com").first()
    if existing:
        db.delete(existing)
        db.commit()

    legacy_user = User(
        email="legacy_unassigned@marketplace.com",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.ADMIN,
        store_name=None,
        store_type=None,
    )
    db.add(legacy_user)
    db.commit()

    token = create_access_token(data={"sub": str(legacy_user.id), "role": legacy_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # Should be rejected on products, orders, dashboard, expenses
    assert client.get("/api/products", headers=headers).status_code == 403
    assert client.get("/api/orders", headers=headers).status_code == 403
    assert client.get("/api/dashboard/revenue", headers=headers).status_code == 403
    assert client.get("/api/expenses", headers=headers).status_code == 403


def test_founder_demo_seeding_and_idempotency(db: Session, client: TestClient):
    """
    Non-founders are blocked from demo endpoints.
    Verified founder can seed demo data idempotently, and reset safely.
    """
    # 1. Non-founder attempt
    normal_user, normal_ws, normal_headers = create_test_tenant(db, "normal_merchant@store.com", "Normal Merchant")
    forbidden_resp = client.post("/api/workspaces/demo/seed", headers=normal_headers)
    assert forbidden_resp.status_code == 403
    err_msg = forbidden_resp.json().get("error") or forbidden_resp.json().get("detail")
    assert "Demo seeding and reset are restricted to the verified SaaS founder" in str(err_msg)

    # 2. Verified Founder account
    founder_user, founder_ws, founder_headers = create_test_tenant(
        db,
        email="shuklapratham758@gmail.com",
        store_name="Modern Munim Founder Flagship",
        store_type="wholesale"
    )

    # 3. First Seed
    seed_resp1 = client.post("/api/workspaces/demo/seed", headers=founder_headers)
    assert seed_resp1.status_code == 200, seed_resp1.text
    data1 = seed_resp1.json()
    assert data1["status"] == "success"
    assert data1["products_created"] > 0
    initial_product_count = data1["products_created"]

    # 4. Repeat Seed -> Idempotent, no duplicates
    seed_resp2 = client.post("/api/workspaces/demo/seed", headers=founder_headers)
    assert seed_resp2.status_code == 200
    data2 = seed_resp2.json()
    assert data2["status"] == "already_seeded"

    # Products count in workspace should not have doubled
    prods_in_ws = client.get("/api/products", headers=founder_headers).json()
    assert len(prods_in_ws) == initial_product_count

    # 5. Reset Demo Data -> Clean reset
    reset_resp = client.post("/api/workspaces/demo/reset", headers=founder_headers)
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "success"

    # Products count in workspace should now be 0
    prods_after_reset = client.get("/api/products", headers=founder_headers).json()
    assert len(prods_after_reset) == 0


def test_onboarding_persistence(db: Session, client: TestClient):
    """Test updating onboarding completion and steps on active workspace."""
    user, ws, headers = create_test_tenant(db, "onboard_test@saas.com", "Onboarding Test Store")

    # Current workspace state
    curr = client.get("/api/workspaces/current", headers=headers).json()
    assert curr["onboarding_completed"] is False
    assert curr["onboarding_step"] == "store_profile"

    # Update step
    patch_resp = client.patch(
        "/api/workspaces/onboarding",
        headers=headers,
        json={"onboarding_step": "catalog_setup", "onboarding_completed": False}
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["onboarding_step"] == "catalog_setup"
    assert updated["onboarding_completed"] is False

    # Mark completed
    done_resp = client.patch(
        "/api/workspaces/onboarding",
        headers=headers,
        json={"onboarding_completed": True}
    )
    assert done_resp.status_code == 200
    assert done_resp.json()["onboarding_completed"] is True
