from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.core.rate_limit import is_rate_limited
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    LoginResponse,
    AuthStartRequest,
    AuthStartResponse,
    AuthOnboardRequest,
    AuthForgotPasswordRequest,
    AuthPasswordUpdateRequest,
    AuthStoreTypesResponse,
    AuthResetPasswordRequest,
)
from app.services import admin_auth_service

router = APIRouter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _user_response(user: User, db: Session | None = None) -> UserResponse:
    from app.services.workspace_service import is_founder_user, get_primary_membership
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    workspace_id = None
    workspace_name = user.store_name
    workspace_slug = None
    is_demo = False
    onboarding_completed = False
    onboarding_step = "store_profile"

    if db is not None:
        membership = get_primary_membership(db, user.id)
        if membership and membership.workspace:
            ws = membership.workspace
            workspace_id = ws.id
            workspace_name = ws.name
            workspace_slug = ws.slug
            is_demo = ws.is_demo
            onboarding_completed = ws.onboarding_completed
            onboarding_step = ws.onboarding_step

    return UserResponse(
        id=user.id,
        email=user.email,
        role=role,
        mfa_enabled=bool(user.mfa_enabled),
        store_name=user.store_name,
        store_type=user.store_type,
        created_at=user.created_at,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        workspace_slug=workspace_slug,
        is_demo=is_demo,
        is_founder=is_founder_user(user),
        onboarding_completed=onboarding_completed,
        onboarding_step=onboarding_step,
    )


def _set_auth_cookie(response: Response, access_token: str) -> None:
    if settings.JWT_COOKIE_NAME:
        response.set_cookie(
            key=settings.JWT_COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


@router.get("/store-types", response_model=AuthStoreTypesResponse)
def list_store_types():
    return AuthStoreTypesResponse(store_types=admin_auth_service.STORE_TYPES)


@router.post("/start", response_model=AuthStartResponse)
def auth_start(
    body: AuthStartRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Email + password → needs_onboarding (new user) or authenticated (issues JWT)."""
    ip = _client_ip(request)
    if is_rate_limited(f"auth-start:{ip}", settings.RATE_LIMIT_LOGIN_PER_MINUTE, 60.0):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
        )
    result = admin_auth_service.start_auth(db, body.email, body.password)
    if result.get("access_token"):
        _set_auth_cookie(response, result["access_token"])
    return AuthStartResponse(
        status=result["status"],
        email=result["email"],
        message=result["message"],
        access_token=result.get("access_token"),
    )


@router.post("/onboard", response_model=AuthStartResponse)
def auth_onboard(
    body: AuthOnboardRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """New user: create admin account with store fields, issue JWT immediately."""
    ip = _client_ip(request)
    if is_rate_limited(f"auth-onboard:{ip}", settings.RATE_LIMIT_LOGIN_PER_MINUTE, 60.0):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
        )
    result = admin_auth_service.complete_onboarding(
        db,
        body.email,
        body.password,
        body.store_name,
        body.store_type,
    )
    if result.get("access_token"):
        _set_auth_cookie(response, result["access_token"])
    return AuthStartResponse(
        status=result["status"],
        email=result["email"],
        message=result["message"],
        access_token=result.get("access_token"),
    )


@router.post("/forgot-password", response_model=AuthStartResponse)
def auth_forgot_password(
    body: AuthResetPasswordRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Forgot password: email + new_password → reset hash → issue JWT.
    No OTP step required.
    """
    ip = _client_ip(request)
    if is_rate_limited(f"auth-forgot:{ip}", settings.RATE_LIMIT_LOGIN_PER_MINUTE, 60.0):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
        )
    result = admin_auth_service.reset_password(db, body.email, body.password)
    if result.get("access_token"):
        _set_auth_cookie(response, result["access_token"])
    return AuthStartResponse(
        status=result["status"],
        email=result["email"],
        message=result["message"],
        access_token=result.get("access_token"),
    )


@router.patch("/password", response_model=UserResponse)
def auth_update_password(
    body: AuthPasswordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Authenticated admin updates their password."""
    user = admin_auth_service.update_password(db, current_user, body.password)
    return _user_response(user)


# ── Disabled legacy endpoints ─────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_400_BAD_REQUEST)
def register_disabled():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Use /api/auth/start and /api/auth/onboard for admin sign-in.",
    )


@router.post("/login", status_code=status.HTTP_400_BAD_REQUEST)
def login_disabled():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Use /api/auth/start for admin sign-in.",
    )


@router.post("/request-otp", status_code=status.HTTP_400_BAD_REQUEST)
def request_otp_disabled():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OTP sign-in is disabled. Use email + password via /api/auth/start.",
    )


@router.post("/resend-otp", status_code=status.HTTP_400_BAD_REQUEST)
def resend_otp_disabled():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OTP sign-in is disabled. Use email + password via /api/auth/start.",
    )


@router.post("/verify-otp", status_code=status.HTTP_400_BAD_REQUEST)
def verify_otp_disabled():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OTP sign-in is disabled. Use email + password via /api/auth/start.",
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Authenticated admin profile (non-admins are rejected)."""
    return _user_response(current_user, db=db)
