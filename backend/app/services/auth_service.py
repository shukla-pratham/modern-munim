from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new customer account. Role from the request body is ignored."""
    email = user_data.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=email,
        password_hash=hashed_password,
        role=UserRole.CUSTOMER,
        mfa_enabled=False,
        mfa_secret=None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticate user and return user object"""
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return user


def create_user_token(user: User) -> str:
    """Create access token for user"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return access_token


def create_mfa_pending_token(user: User) -> str:
    """Short-lived token proving password was accepted; MFA code still required."""
    return create_access_token(
        data={"sub": str(user.id), "mfa_pending": True},
        expires_delta=timedelta(minutes=5),
    )
