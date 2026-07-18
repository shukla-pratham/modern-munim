from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limit import is_rate_limited
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.auth_service import create_user, authenticate_user, create_user_token

router = APIRouter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    user = create_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login and get access token. Optionally sets HTTPOnly cookie when JWT_COOKIE_NAME is set."""
    ip = _client_ip(request)
    if is_rate_limited(f"login:{ip}", settings.RATE_LIMIT_LOGIN_PER_MINUTE, 60.0):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )
    user = authenticate_user(db, form_data.username, form_data.password)
    access_token = create_user_token(user)
    out = {"access_token": access_token, "token_type": "bearer"}
    if settings.JWT_COOKIE_NAME:
        response.set_cookie(
            key=settings.JWT_COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    return out


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user
