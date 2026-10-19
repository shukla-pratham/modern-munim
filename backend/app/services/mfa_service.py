"""TOTP MFA helpers (Authenticator-app based)."""
from __future__ import annotations

import base64
from typing import Optional

import pyotp
import qrcode
import qrcode.image.svg
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User


ISSUER = "Modern Munim"


def generate_secret() -> str:
    return pyotp.random_base32()


def build_otpauth_url(email: str, secret: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def qr_svg_base64(otpauth_url: str) -> str:
    """SVG QR (no Pillow required)."""
    img = qrcode.make(otpauth_url, image_factory=qrcode.image.svg.SvgPathImage)
    svg_bytes = img.to_string()
    if isinstance(svg_bytes, str):
        svg_bytes = svg_bytes.encode("utf-8")
    return base64.b64encode(svg_bytes).decode("ascii")


def verify_totp(secret: Optional[str], code: str) -> bool:
    if not secret:
        return False
    cleaned = (code or "").strip().replace(" ", "")
    if not cleaned.isdigit():
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(cleaned, valid_window=1))


def begin_setup(db: Session, user: User) -> tuple[str, str, str]:
    """Store a pending secret (not enabled yet) and return provisioning data."""
    secret = generate_secret()
    user.mfa_secret = secret
    user.mfa_enabled = False
    db.add(user)
    db.commit()
    db.refresh(user)
    url = build_otpauth_url(user.email, secret)
    return secret, url, qr_svg_base64(url)


def enable(db: Session, user: User, code: str) -> User:
    if not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not started. Call /api/auth/mfa/setup first.",
        )
    if not verify_totp(user.mfa_secret, code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authenticator code",
        )
    user.mfa_enabled = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def disable(db: Session, user: User) -> User:
    user.mfa_enabled = False
    user.mfa_secret = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
