from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Optional[str] = "customer"
    store_name: Optional[str] = None
    store_type: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    mfa_enabled: bool = False
    store_name: Optional[str] = None
    store_type: Optional[str] = None
    created_at: datetime
    workspace_id: Optional[int] = None
    workspace_name: Optional[str] = None
    workspace_slug: Optional[str] = None
    is_demo: bool = False
    is_founder: bool = False
    onboarding_completed: bool = False
    onboarding_step: str = "store_profile"

    class Config:
        from_attributes = True


class AuthStartRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthStartResponse(BaseModel):
    status: str  # needs_onboarding | authenticated
    email: str
    message: str
    access_token: Optional[str] = None


class AuthOnboardRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    store_name: str = Field(min_length=2, max_length=200)
    store_type: str = Field(min_length=1, max_length=100)


class AuthResetPasswordRequest(BaseModel):
    """Forgot-password: supply email + new password (no OTP required)."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthForgotPasswordRequest(BaseModel):
    """Kept for backward-compat import; use AuthResetPasswordRequest for new code."""
    email: EmailStr


class AuthPasswordUpdateRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class AuthStoreTypesResponse(BaseModel):
    store_types: list[str]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    mfa_required: bool = False
    mfa_token: Optional[str] = None


class TokenData(BaseModel):
    user_id: Optional[int] = None


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_base64: str
    mfa_enabled: bool


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class MfaVerifyLoginRequest(BaseModel):
    mfa_token: str
    code: str = Field(min_length=6, max_length=8)


class MfaDisableRequest(BaseModel):
    password: str
    code: str = Field(min_length=6, max_length=8)


