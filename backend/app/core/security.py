from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import bcrypt

# Optimize bcrypt rounds for faster verification (development)
# Production should use default rounds (12) for security
# Using rounds=4 for development speed (default is 12, which is ~0.2s per verify)
import os
bcrypt_rounds = 4 if os.getenv("ENVIRONMENT") == "development" else 12

# Configure passlib with explicit backend to avoid compatibility issues
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=bcrypt_rounds,
    bcrypt__ident="2b"  # Use bcrypt 2b format explicitly
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Truncate password to 72 bytes if longer (bcrypt limit)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        return pwd_context.verify(password_bytes.decode('utf-8', errors='ignore'), hashed_password)
    except (ValueError, TypeError) as e:
        # Fallback to direct bcrypt if passlib fails
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except:
            return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    try:
        # Truncate password to 72 bytes if longer (bcrypt limit)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        return pwd_context.hash(password_bytes.decode('utf-8', errors='ignore'))
    except (ValueError, TypeError) as e:
        # Fallback to direct bcrypt if passlib fails
        salt = bcrypt.gensalt(rounds=bcrypt_rounds)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.
    Returns None if token is invalid, expired, or malformed.
    Handles expiration gracefully (JWTError includes ExpiredSignatureError).
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        # Token is invalid, expired, or malformed
        # Return None to indicate authentication failure
        # Specific error handling can be added here if needed for logging
        return None
