"""
Isolated admin auth flow tests — password-only (no OTP).

Uses TEST_DATABASE_URL if set, otherwise DATABASE_URL from the environment.
Creates unique emails per run and deletes those rows in teardown.
"""
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
from app.core.security import get_password_hash, verify_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


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
def unique_email() -> str:
    return f"auth_test_{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def cleanup_email(db: Session, unique_email: str):
    yield unique_email
    db.query(User).filter(User.email == unique_email).delete()
    db.commit()


def _err(resp) -> str:
    body = resp.json()
    if isinstance(body.get("error"), str):
        return body["error"]
    return str(body.get("detail", body))


# ── Basic start endpoint ──────────────────────────────────────────────────────

def test_new_email_returns_needs_onboarding(client: TestClient, cleanup_email: str):
    r = client.post("/api/auth/start", json={"email": cleanup_email, "password": "securepass1"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "needs_onboarding"
    assert "new" in body["message"].lower()


def test_wrong_password_returns_401(client: TestClient, db: Session, cleanup_email: str):
    db.add(User(
        email=cleanup_email,
        password_hash=get_password_hash("securepass1"),
        role=UserRole.ADMIN,
        store_name="Test Shop",
        store_type="Grocery",
    ))
    db.commit()
    r = client.post("/api/auth/start", json={"email": cleanup_email, "password": "wrongpass1"})
    assert r.status_code == 401


def test_correct_password_returns_authenticated_with_token(
    client: TestClient, db: Session, cleanup_email: str
):
    db.add(User(
        email=cleanup_email,
        password_hash=get_password_hash("securepass1"),
        role=UserRole.ADMIN,
        store_name="Token Shop",
        store_type="Grocery",
    ))
    db.commit()
    r = client.post("/api/auth/start", json={"email": cleanup_email, "password": "securepass1"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "authenticated"
    assert body.get("access_token"), "JWT must be present in response"


# ── Onboarding ────────────────────────────────────────────────────────────────

def test_onboard_requires_store_name(client: TestClient, cleanup_email: str):
    r = client.post("/api/auth/onboard", json={
        "email": cleanup_email,
        "password": "securepass1",
        "store_name": "",
        "store_type": "Bakery",
    })
    assert r.status_code == 422


def test_onboard_rejects_invalid_store_type(client: TestClient, cleanup_email: str):
    r = client.post("/api/auth/onboard", json={
        "email": cleanup_email,
        "password": "securepass1",
        "store_name": "My Store",
        "store_type": "NotARealType",
    })
    assert r.status_code == 400
    assert "store type" in _err(r).lower()


def test_onboard_creates_admin_and_issues_token(
    client: TestClient, db: Session, cleanup_email: str
):
    # Start confirms unknown email
    start = client.post("/api/auth/start", json={"email": cleanup_email, "password": "securepass1"})
    assert start.json()["status"] == "needs_onboarding"

    # Onboard creates user and immediately issues JWT
    onboard = client.post("/api/auth/onboard", json={
        "email": cleanup_email,
        "password": "securepass1",
        "store_name": "Sunrise Bakery",
        "store_type": "Bakery",
    })
    assert onboard.status_code == 200
    body = onboard.json()
    assert body["status"] == "authenticated"
    token = body.get("access_token")
    assert token, "JWT must be present after onboarding"

    # Password is hashed in DB
    user = db.query(User).filter(User.email == cleanup_email).first()
    assert user is not None
    assert user.role == UserRole.ADMIN or (
        hasattr(user.role, "value") and user.role.value == "admin"
    )
    assert user.password_hash != "securepass1"
    assert verify_password("securepass1", user.password_hash)
    assert user.store_name == "Sunrise Bakery"

    # Token works for /me
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    # No raw code in response body
    assert "code" not in body
    assert body.get("status") != "otp_sent"


# ── Login flow ────────────────────────────────────────────────────────────────

def test_existing_user_login_flow(client: TestClient, db: Session, cleanup_email: str):
    db.add(User(
        email=cleanup_email,
        password_hash=get_password_hash("securepass1"),
        role=UserRole.ADMIN,
        store_name="Existing Shop",
        store_type="Electronics",
    ))
    db.commit()

    # Wrong password → 401
    wrong = client.post("/api/auth/start", json={"email": cleanup_email, "password": "wrongpassword"})
    assert wrong.status_code == 401

    # Correct password → JWT in response
    start = client.post("/api/auth/start", json={"email": cleanup_email, "password": "securepass1"})
    assert start.status_code == 200
    assert start.json()["status"] == "authenticated"
    token = start.json().get("access_token")
    assert token

    # Token grants dashboard access
    dash = client.get("/api/dashboard/revenue?days=7", headers={"Authorization": f"Bearer {token}"})
    assert dash.status_code == 200


# ── Forgot password ───────────────────────────────────────────────────────────

def test_forgot_password_resets_and_issues_token(
    client: TestClient, db: Session, cleanup_email: str
):
    db.add(User(
        email=cleanup_email,
        password_hash=get_password_hash("oldpassword1"),
        role=UserRole.ADMIN,
        store_name="Recover Store",
        store_type="Pharmacy",
    ))
    db.commit()

    # Unknown email → 400
    unknown = client.post("/api/auth/forgot-password", json={
        "email": "nobody_xyz@example.com",
        "password": "newpassword1",
    })
    assert unknown.status_code == 400

    # Known email → password reset + token
    forgot = client.post("/api/auth/forgot-password", json={
        "email": cleanup_email,
        "password": "newpassword1",
    })
    assert forgot.status_code == 200
    body = forgot.json()
    assert body["status"] == "authenticated"
    token = body.get("access_token")
    assert token

    # Verify new password is hashed and old is gone
    db.expire_all()
    user = db.query(User).filter(User.email == cleanup_email).first()
    assert verify_password("newpassword1", user.password_hash)
    assert not verify_password("oldpassword1", user.password_hash)

    # New password works for normal login
    start = client.post("/api/auth/start", json={"email": cleanup_email, "password": "newpassword1"})
    assert start.status_code == 200
    assert start.json()["status"] == "authenticated"


# ── Authenticated password update ─────────────────────────────────────────────

def test_authenticated_password_update(client: TestClient, db: Session, cleanup_email: str):
    user = User(
        email=cleanup_email,
        password_hash=get_password_hash("oldpass123"),
        role=UserRole.ADMIN,
        store_name="PW Update Shop",
        store_type="Other",
    )
    db.add(user)
    db.commit()

    from app.services.auth_service import create_user_token
    token = create_user_token(user)

    # Unauthenticated → 401
    bare = client.patch("/api/auth/password", json={"password": "newpass123"})
    assert bare.status_code == 401

    # Authenticated → success
    updated = client.patch(
        "/api/auth/password",
        json={"password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert updated.status_code == 200

    db.expire_all()
    user = db.query(User).filter(User.email == cleanup_email).first()
    assert verify_password("newpass123", user.password_hash)
    assert not verify_password("oldpass123", user.password_hash)


# ── Authorization guards ──────────────────────────────────────────────────────

def test_unauthenticated_and_non_admin_blocked(client: TestClient, db: Session, cleanup_email: str):
    unauth = client.get("/api/dashboard/revenue?days=7")
    assert unauth.status_code == 401

    user = User(
        email=cleanup_email,
        password_hash=get_password_hash("securepass1"),
        role=UserRole.CUSTOMER,
        store_name="Cust",
        store_type="Other",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    from app.services.auth_service import create_user_token
    token = create_user_token(user)

    forbidden = client.get("/api/dashboard/revenue?days=7", headers={"Authorization": f"Bearer {token}"})
    assert forbidden.status_code == 403

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 403


def test_orders_require_admin(client: TestClient, db: Session, cleanup_email: str):
    assert client.get("/api/orders").status_code == 401

    customer = User(
        email=cleanup_email,
        password_hash=get_password_hash("securepass1"),
        role=UserRole.CUSTOMER,
        store_name="Cust",
        store_type="Other",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    from app.services.auth_service import create_user_token
    cust_token = create_user_token(customer)

    assert client.get("/api/orders", headers={"Authorization": f"Bearer {cust_token}"}).status_code == 403

    # Promote to admin and login directly
    customer.role = UserRole.ADMIN
    db.add(customer)
    db.commit()

    start = client.post("/api/auth/start", json={"email": cleanup_email, "password": "securepass1"})
    assert start.status_code == 200
    admin_token = start.json()["access_token"]

    assert client.get("/api/orders", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200
    assert client.get("/api/orders/my-orders", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200


def test_product_reads_require_admin(client: TestClient):
    assert client.get("/api/products").status_code == 401
    assert client.get("/api/products/1").status_code == 401


# ── Legacy / disabled endpoints ───────────────────────────────────────────────

def test_legacy_otp_only_disabled(client: TestClient):
    r = client.post("/api/auth/request-otp", json={"email": "x@example.com", "store_name": "S"})
    assert r.status_code == 400
    assert "disabled" in _err(r).lower()


def test_verify_otp_endpoint_disabled(client: TestClient):
    r = client.post("/api/auth/verify-otp", json={"email": "x@example.com", "code": "123456"})
    assert r.status_code == 400
    assert "disabled" in _err(r).lower()


def test_resend_otp_endpoint_disabled(client: TestClient):
    r = client.post("/api/auth/resend-otp", json={"email": "x@example.com"})
    assert r.status_code == 400
    assert "disabled" in _err(r).lower()


# ── Codebase hygiene ──────────────────────────────────────────────────────────

def test_no_startup_mock_user_logic():
    main_src = (BACKEND_ROOT / "app" / "main.py").read_text()
    assert "DELETE FROM users" not in main_src
    assert "DELETE FROM orders" not in main_src
    assert "seed_users" not in main_src

    seed_src = (BACKEND_ROOT / "app" / "seed_data.py").read_text()
    assert "admin@marketplace.com" not in seed_src or "Skipping user seed" in seed_src
    assert 'email="admin@marketplace.com"' not in seed_src
    assert "abcd@fufu.com" not in seed_src
