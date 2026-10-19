"""
DEPRECATED: OTP-only sign-in has been replaced by admin_auth_service
(email + password + optional onboarding + OTP).

Kept as a stub so accidental imports fail clearly.
"""

from fastapi import HTTPException, status


def request_otp(*_args, **_kwargs):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OTP-only sign-in is disabled. Use /api/auth/start.",
    )


def verify_otp(*_args, **_kwargs):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OTP-only sign-in is disabled. Use /api/auth/start → verify-otp.",
    )
