"""
Admin-only auth — email + password, no OTP gate.

Flows:
  Signup:  email + password + store fields → create admin → issue JWT
  Login:   email + password → verify hash → issue JWT
  Forgot:  email + new_password → verify email exists → update hash → issue JWT
  Password update: authenticated admin sets new password
"""
from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.services.auth_service import create_user_token

logger = logging.getLogger(__name__)

STORE_TYPES = [
    "Bakery",
    "Confectionery",
    "Grocery",
    "Clothing",
    "Electronics",
    "Pharmacy",
    "Restaurant / Cafe",
    "General Retail",
    "Other",
]


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _role_value(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _build_token_result(db: Session, user: User) -> dict:
    """Issue JWT and collect workspace context."""
    from app.services.workspace_service import ensure_user_workspace, is_founder_user

    ws, _membership = ensure_user_workspace(db, user)
    token = create_user_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": _role_value(user),
            "store_name": user.store_name,
            "store_type": user.store_type,
            "workspace_id": ws.id if ws else None,
            "workspace_name": ws.name if ws else None,
            "workspace_slug": ws.slug if ws else None,
            "is_demo": bool(ws.is_demo) if ws else False,
            "is_founder": is_founder_user(user),
            "onboarding_completed": bool(ws.onboarding_completed) if ws else False,
            "onboarding_step": ws.onboarding_step if ws else "store_profile",
        },
    }


def start_auth(db: Session, email: str, password: str) -> dict:
    """
    Step 1 of login — also the final step now (no OTP).

    Returns:
      {"status": "needs_onboarding", ...}  — email not found, client proceeds to onboard
      {"status": "authenticated", "access_token": ...}  — correct password, JWT issued
    Raises 401 on wrong password.
    """
    email = _normalize_email(email)
    if not email or "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid email is required")
    if not password or len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return {
            "status": "needs_onboarding",
            "email": email,
            "message": "Looks like you're new here.",
        }

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if _role_value(user) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    result = _build_token_result(db, user)
    return {
        "status": "authenticated",
        "email": email,
        "message": "Signed in successfully.",
        **result,
    }


def complete_onboarding(
    db: Session,
    email: str,
    password: str,
    store_name: str,
    store_type: str,
) -> dict:
    """Create new admin account and issue JWT immediately — no OTP."""
    email = _normalize_email(email)
    store_name = (store_name or "").strip()
    store_type = (store_type or "").strip()

    if not email or "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid email is required")
    if not password or len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    if len(store_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Store name is required",
        )
    if store_type not in STORE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select a valid store type",
        )

    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to complete onboarding for this email. Sign in with your password instead.",
        )

    user = User(
        email=email,
        password_hash=get_password_hash(password),
        role=UserRole.ADMIN,
        store_name=store_name,
        store_type=store_type,
        mfa_enabled=False,
        mfa_secret=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    from app.services.workspace_service import create_user_workspace, is_founder_user
    is_demo = is_founder_user(user)
    create_user_workspace(
        db,
        user=user,
        store_name=store_name,
        store_type=store_type,
        is_demo=is_demo,
    )
    db.commit()

    result = _build_token_result(db, user)
    return {
        "status": "authenticated",
        "email": email,
        "message": "Account created. Welcome to Modern Munim!",
        **result,
    }


def reset_password(db: Session, email: str, new_password: str) -> dict:
    """
    Forgot-password flow — no OTP.
    Caller provides email + new password. If the account exists, password is reset
    and a JWT is issued. If the email does not exist, we raise 400 (no account enumeration
    concern here since this is an admin-only product).
    """
    email = _normalize_email(email)
    if not email or "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid email is required")
    if not new_password or len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No account found for this email.",
        )

    user.password_hash = get_password_hash(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    result = _build_token_result(db, user)
    return {
        "status": "authenticated",
        "email": email,
        "message": "Password updated. Signed in.",
        **result,
    }


def update_password(db: Session, user: User, new_password: str) -> User:
    """Authenticated admin sets a new password."""
    if not new_password or len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
