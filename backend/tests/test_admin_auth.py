"""
Isolated admin auth flow tests.

Uses TEST_DATABASE_URL if set, otherwise DATABASE_URL from the environment.
Creates unique emails per run and deletes those rows in teardown — never seeds
demo accounts into the shared runtime DB permanently.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Ensure backend package is importable
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import get_password_hash, verify_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.email_otp import EmailOtp  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.services import admin_auth_service  # noqa: E402


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    # TrustedHostMiddleware rejects Host: testserver; use localhost.
    return TestClient(app, base_url="http://localhost")


@pytest.fixture
def unique_email() -> str:
    return f"auth_test_{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def cleanup_email(db: Session, unique_email: str):
    yield unique_email
    db.query(EmailOtp).filter(EmailOtp.email == unique_email).delete()
    db.query(User).filter(User.email == unique_email).delete()
    db.commit()


def _read_otp_from_db(db: Session, email: str, plaintext_candidates: list[str] | None = None) -> str:
    """
    Recover OTP for tests by re-issuing with a monkeypatched generator,
    or by brute-forcing against the hash when the code is known from patch.
    Prefer calling with a known code via monkeypatch.
    """
    raise RuntimeError("use monkeypatched OTP")


@pytest.fixture
def capture_otp(monkeypatch):
    """Force a known OTP so tests never need SMTP or log scraping."""
    known = {"code": "482913"}

    def fake_issue(db: Session, email: str, store_name: str | None = None) -> str:
        from app.core.config import settings
        from app.core.security import get_password_hash
        from app.models.email_otp import EmailOtp
        from datetime import datetime, timedelta, timezone

        code = known["code"]
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_OTP_EXPIRE_MINUTES)
        row = db.query(EmailOtp).filter(EmailOtp.email == email).first()
        if row is None:
            row = EmailOtp(email=email)
            db.add(row)
        row.code_hash = get_password_hash(code)
        row.store_name = store_name
        row.expires_at = expires
        row.attempt_count = 0
        db.commit()
        return "log"  # delivery mode expected by callers

    monkeypatch.setattr(admin_auth_service, "_issue_otp", fake_issue)
    return known


def test_new_email_starts_registration(client: TestClient, cleanup_email: str):
    r = client.post("/api/auth/start", json={"email": cleanup_email, "password": "securepass1"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "needs_onboarding"
    assert "new" in body["message"].lower()


def test_new_user_requires_store_name(client: TestClient, cleanup_email: str, capture_otp):
    client.post("/api/auth/start", json={"email": cleanup_email, "password": "securepass1"})
    r = client.post(
        "/api/auth/onboard",
        json={
            "email": cleanup_email,
            "password": "securepass1",
            "store_name": "",
            "store_type": "Bakery",
        },
    )
    assert r.status_code == 422


def _err(resp) -> str:
    body = resp.json()
    if isinstance(body.get("error"), str):
        return body["error"]
    return str(body.get("detail", body))


def test_new_user_requires_store_type(client: TestClient, cleanup_email: str, capture_otp):
    r = client.post(
        "/api/auth/onboard",
        json={
            "email": cleanup_email,
            "password": "securepass1",
            "store_name": "Test Store",
            "store_type": "NotARealType",
        },
    )
    assert r.status_code == 400
    assert "store type" in _err(r).lower()


def test_new_account_admin_hashed_password_otp_and_login(
    client: TestClient, db: Session, cleanup_email: str, capture_otp
):
    start = client.post("/api/auth/start", json={"email": cleanup_email, "password": "securepass1"})
    assert start.json()["status"] == "needs_onboarding"

    onboard = client.post(
        "/api/auth/onboard",
        json={
            "email": cleanup_email,
            "password": "securepass1",
            "store_name": "Sunrise Bakery",
            "store_type": "Bakery",
        },
    )
    assert onboard.status_code == 200
    assert onboard.json()["status"] == "otp_sent"
    assert "code" not in onboard.json()
    assert "otp" not in onboard.text.lower() or "otp_sent" in onboard.text

    user = db.query(User).filter(User.email == cleanup_email).first()
    assert user is not None
    assert user.role == UserRole.ADMIN or (
        hasattr(user.role, "value") and user.role.value == "admin"
    )
    assert user.password_hash != "securepass1"
    assert verify_password("securepass1", user.password_hash)
    assert user.store_name == "Sunrise Bakery"
    assert user.store_type == "Bakery"

    bad = client.post(
        "/api/auth/verify-otp",
        json={"email": cleanup_email, "code": "000000"},
    )
    assert bad.status_code == 401

    ok = client.post(
        "/api/auth/verify-otp",
        json={"email": cleanup_email, "code": capture_otp["code"]},
    )
    assert ok.status_code == 200
    token = ok.json()["access_token"]
    assert token

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    # OTP single-use
    reuse = client.post(
        "/api/auth/verify-otp",
        json={"email": cleanup_email, "code": capture_otp["code"]},
    )
    assert reuse.status_code == 400


def test_expired_otp_rejected(client: TestClient, db: Session, cleanup_email: str, capture_otp):
    client.post(
        "/api/auth/onboard",
        json={
            "email": cleanup_email,
            "password": "securepass1",
            "store_name": "Expire Store",
            "store_type": "Grocery",
        },
    )
    row = db.query(EmailOtp).filter(EmailOtp.email == cleanup_email).first()
    assert row is not None
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.add(row)
    db.commit()

    r = client.post(
        "/api/auth/verify-otp",
        json={"email": cleanup_email, "code": capture_otp["code"]},
    )
    assert r.status_code == 400
    assert "expired" in _err(r).lower()


def test_existing_user_login_flow(client: TestClient, db: Session, cleanup_email: str, capture_otp):
    user = User(
        email=cleanup_email,
        password_hash=get_password_hash("securepass1"),
        role=UserRole.ADMIN,
        store_name="Existing Shop",
        store_type="Electronics",
    )
    db.add(user)
    db.commit()

    wrong = client.post(
        "/api/auth/start",
        json={"email": cleanup_email, "password": "wrongpassword"},
    )
    assert wrong.status_code == 401

    start = client.post(
        "/api/auth/start",
        json={"email": cleanup_email, "password": "securepass1"},
    )
    assert start.status_code == 200
    assert start.json()["status"] == "otp_sent"
    assert start.json()["status"] != "needs_onboarding"

    bad_otp = client.post(
        "/api/auth/verify-otp",
        json={"email": cleanup_email, "code": "111111"},
    )
    assert bad_otp.status_code == 401

    ok = client.post(
        "/api/auth/verify-otp",
        json={"email": cleanup_email, "code": capture_otp["code"]},
    )
    assert ok.status_code == 200
    token = ok.json()["access_token"]

    dash = client.get(
        "/api/dashboard/revenue?days=7",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dash.status_code == 200


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
    forbidden = client.get(
        "/api/dashboard/revenue?days=7",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert forbidden.status_code == 403

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 403


def test_no_startup_mock_user_logic():
    main_src = (BACKEND_ROOT / "app" / "main.py").read_text()
    assert "DELETE FROM users" not in main_src
    assert "DELETE FROM orders" not in main_src
    assert "seed_users" not in main_src

    seed_src = (BACKEND_ROOT / "app" / "seed_data.py").read_text()
    assert "admin@marketplace.com" not in seed_src or "Skipping user seed" in seed_src
    # seed_users must not create the old demo emails
    assert 'email="admin@marketplace.com"' not in seed_src
    assert "abcd@fufu.com" not in seed_src


def test_legacy_otp_only_disabled(client: TestClient):
    r = client.post("/api/auth/request-otp", json={"email": "x@example.com", "store_name": "S"})
    assert r.status_code == 400
    assert "disabled" in _err(r).lower()


def test_forgot_password_otp_then_login_then_reset(
    client: TestClient, db: Session, cleanup_email: str, capture_otp
):
    user = User(
        email=cleanup_email,
        password_hash=get_password_hash("oldpassword1"),
        role=UserRole.ADMIN,
        store_name="Recover Store",
        store_type="Pharmacy",
    )
    db.add(user)
    db.commit()

    unknown = client.post("/api/auth/forgot-password", json={"email": "nobody_xyz@example.com"})
    assert unknown.status_code == 200
    assert unknown.json()["status"] == "otp_sent"

    forgot = client.post("/api/auth/forgot-password", json={"email": cleanup_email})
    assert forgot.status_code == 200
    assert forgot.json()["status"] == "otp_sent"

    # Cannot reset password before OTP login
    bare = client.patch("/api/auth/password", json={"password": "newpassword1"})
    assert bare.status_code == 401

    verify = client.post(
        "/api/auth/verify-otp",
        json={"email": cleanup_email, "code": capture_otp["code"]},
    )
    assert verify.status_code == 200
    token = verify.json()["access_token"]

    updated = client.patch(
        "/api/auth/password",
        json={"password": "newpassword1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert updated.status_code == 200

    db.refresh(user)
    assert verify_password("newpassword1", user.password_hash)
    assert not verify_password("oldpassword1", user.password_hash)

    # New password works for normal start → OTP path
    start = client.post(
        "/api/auth/start",
        json={"email": cleanup_email, "password": "newpassword1"},
    )
    assert start.status_code == 200
    assert start.json()["status"] == "otp_sent"


def test_orders_require_admin(client: TestClient, db: Session, cleanup_email: str, capture_otp):
    """Order APIs are admin-only: 401 unauth, 403 non-admin, 200 admin."""
    unauth = client.get("/api/orders")
    assert unauth.status_code == 401

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
    forbidden = client.get(
        "/api/orders",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert forbidden.status_code == 403

    forbidden_mine = client.get(
        "/api/orders/my-orders",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert forbidden_mine.status_code == 403

    # Promote via normal OTP login path (existing user)
    customer.role = UserRole.ADMIN
    db.add(customer)
    db.commit()

    start = client.post(
        "/api/auth/start",
        json={"email": cleanup_email, "password": "securepass1"},
    )
    assert start.status_code == 200
    ok = client.post(
        "/api/auth/verify-otp",
        json={"email": cleanup_email, "code": capture_otp["code"]},
    )
    assert ok.status_code == 200
    admin_token = ok.json()["access_token"]

    allowed = client.get(
        "/api/orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert allowed.status_code == 200

    allowed_mine = client.get(
        "/api/orders/my-orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert allowed_mine.status_code == 200


def test_product_reads_require_admin(client: TestClient):
    open_list = client.get("/api/products")
    assert open_list.status_code == 401
    open_one = client.get("/api/products/1")
    assert open_one.status_code == 401

