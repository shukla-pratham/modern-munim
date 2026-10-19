"""
Admin-only auth:

Existing: email + password → OTP → admin session
New: email + password → onboarding (store_name, store_type) → create admin → OTP → session
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.email_otp import EmailOtp
from app.models.user import User, UserRole
from app.services.auth_service import create_user_token
from app.services.email_service import send_login_otp

logger = logging.getLogger(__name__)

MAX_OTP_ATTEMPTS = 5

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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _role_value(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _issue_otp(db: Session, email: str, store_name: str | None = None) -> str:
    """Persist OTP hash and deliver code. Returns delivery mode: 'smtp' | 'log'."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires = _utcnow() + timedelta(minutes=settings.EMAIL_OTP_EXPIRE_MINUTES)
    row = db.query(EmailOtp).filter(EmailOtp.email == email).first()
    if row is None:
        row = EmailOtp(email=email)
        db.add(row)
    row.code_hash = get_password_hash(code)
    row.store_name = store_name
    row.expires_at = expires
    row.attempt_count = 0
    db.commit()
    return send_login_otp(email, code, store_name)


def _otp_message(email: str, delivery: str = "resend") -> str:
    if delivery in ("resend", "smtp"):
        return f"A 6-digit code was sent to {email}."
    return (
        f"A 6-digit code was generated for {email}. "
        "Email delivery was unavailable — check the FastAPI server log for the OTP (development only)."
    )


def start_auth(db: Session, email: str, password: str) -> dict:
    """
    Step 1: email + password.
    - Existing user + correct password → send OTP
    - New email → needs_onboarding (account not created yet)
    - Existing + wrong password → generic failure
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

    delivery = _issue_otp(db, email, user.store_name)
    return {
        "status": "otp_sent",
        "email": email,
        "message": _otp_message(email, delivery),
    }


def complete_onboarding(
    db: Session,
    email: str,
    password: str,
    store_name: str,
    store_type: str,
) -> dict:
    """Create a new admin account, then send OTP."""
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
        # Do not say "already exists" — steer into the normal login path.
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

    delivery = _issue_otp(db, email, store_name)
    return {
        "status": "otp_sent",
        "email": email,
        "message": _otp_message(email, delivery),
    }


def start_forgot_password(db: Session, email: str) -> dict:
    """
    Forgot password: email → OTP (no password).
    Always returns a generic otp_sent-style response (no account enumeration).
    OTP is only issued when the email exists.
    """
    email = _normalize_email(email)
    if not email or "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid email is required")

    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        delivery = _issue_otp(db, email, user.store_name)
        return {
            "status": "otp_sent",
            "email": email,
            "message": _otp_message(email, delivery),
        }

    # Same shape as success; do not reveal that the email is unknown.
    return {
        "status": "otp_sent",
        "email": email,
        "message": (
            f"If an account exists for {email}, a 6-digit code was sent. "
            "Check your email (or the API server log in development)."
        ),
    }


def update_password(db: Session, user: User, new_password: str) -> User:
    """Authenticated admin sets a new password (used after OTP login recovery)."""
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


def resend_otp(db: Session, email: str) -> dict:
    email = _normalize_email(email)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification for this email. Start sign-in again.",
        )
    delivery = _issue_otp(db, email, user.store_name)
    return {
        "status": "otp_sent",
        "email": email,
        "message": _otp_message(email, delivery),
    }


def verify_otp(db: Session, email: str, code: str) -> dict:
    email = _normalize_email(email)
    cleaned = (code or "").strip().replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter the 6-digit code from your email",
        )

    row = db.query(EmailOtp).filter(EmailOtp.email == email).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP requested for this email. Request a new code.",
        )

    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if _utcnow() > expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Request a new code.",
        )
    if int(row.attempt_count or 0) >= MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Request a new code.",
        )

    if not verify_password(cleaned, row.code_hash):
        row.attempt_count = int(row.attempt_count or 0) + 1
        db.add(row)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account not found. Start sign-in again.",
        )

    # App is admin-only: ensure role after successful OTP.
    user.role = UserRole.ADMIN
    db.add(user)
    db.delete(row)  # single-use
    db.commit()
    db.refresh(user)

    if _role_value(user) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    from app.services.workspace_service import ensure_user_workspace, is_founder_user
    ws, membership = ensure_user_workspace(db, user)

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
