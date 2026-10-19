from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Union
import os


class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="", description="PostgreSQL database URL")
    SECRET_KEY: str = Field(default="", description="Secret key for JWT tokens (min 32 chars)")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440, description="Token expiration in minutes")
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
        description="Allowed CORS origins (comma-separated); no wildcards in production"
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1",
        description="Comma-separated list of allowed host headers"
    )
    DEBUG: bool = Field(default=False, description="Debug mode; must be False in production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production/staging)")
    AI_BATCH_JOB_TIMEOUT_HOURS: int = Field(default=2, ge=1, description="Hours before job is considered stale")
    RATE_LIMIT_LOGIN_PER_MINUTE: int = Field(default=10, ge=1, le=120, description="Max login attempts per IP per minute")
    JWT_COOKIE_NAME: str = Field(default="", description="If set, login also sets an HTTPOnly cookie with the token")
    # Gmail / SMTP for email OTP (use a Google App Password, not your normal password)
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP host")
    SMTP_PORT: int = Field(default=587, ge=1, le=65535, description="SMTP port")
    SMTP_USER: str = Field(default="", description="SMTP username (your Gmail address)")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password / Gmail App Password")
    SMTP_FROM: str = Field(default="", description="From address (defaults to SMTP_USER)")
    EMAIL_OTP_EXPIRE_MINUTES: int = Field(default=10, ge=1, le=60, description="Email OTP lifetime")
    EMAIL_OTP_DEV_LOG: bool = Field(
        default=True,
        description="Log OTP codes to server logs in development when SMTP is missing or for debugging",
    )
    RESEND_API_KEY: str = Field(default="", description="Resend API key (re_...) for HTTPS email delivery")
    RESEND_FROM_EMAIL: str = Field(default="onboarding@resend.dev", description="Sender email address for Resend")

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            origins = [o.strip() for o in v.split(",") if o.strip()]
            return origins if origins else ["http://localhost:3000"]
        return ["http://localhost:3000"]

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if not v:
            return v
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v:
            return v
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    def get_allowed_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    def get_cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [o.strip() for o in str(self.CORS_ORIGINS).split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


def enforce_production_mail(settings_obj) -> None:
    """Production must email OTPs (via Resend HTTPS API or SMTP) and must not log them."""
    if getattr(settings_obj, "ENVIRONMENT", "") != "production":
        return
    has_resend = bool(getattr(settings_obj, "RESEND_API_KEY", "").strip())
    has_smtp = bool(getattr(settings_obj, "SMTP_USER", "").strip() and getattr(settings_obj, "SMTP_PASSWORD", "").strip())
    if not (has_resend or has_smtp):
        raise ValueError(
            "Either RESEND_API_KEY (recommended for Render free tier HTTPS delivery) or "
            "(SMTP_USER and SMTP_PASSWORD) is required in production so login OTPs can be emailed."
        )
    if getattr(settings_obj, "EMAIL_OTP_DEV_LOG", False):
        raise ValueError(
            "EMAIL_OTP_DEV_LOG must be false in production. OTPs must not be written to logs."
        )


def _validate_production():
    env = os.getenv("ENVIRONMENT", "development")
    if env != "production":
        return
    if os.getenv("DEBUG", "").lower() in ("1", "true", "yes"):
        raise ValueError(
            "ENVIRONMENT=production but DEBUG is True. Set DEBUG=false in production."
        )
    db = os.getenv("DATABASE_URL", "")
    if not db or not db.startswith(("postgresql://", "postgresql+psycopg2://")):
        raise ValueError(
            "DATABASE_URL is required in production and must be a PostgreSQL connection string."
        )
    sk = os.getenv("SECRET_KEY", "")
    if not sk or len(sk) < 32:
        raise ValueError(
            "SECRET_KEY is required in production and must be at least 32 characters. "
            "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    cors = os.getenv("CORS_ORIGINS", "")
    if "*" in cors or cors.strip() == "":
        raise ValueError(
            "CORS_ORIGINS in production must be explicit origins (comma-separated). No wildcards."
        )


try:
    _validate_production()
except ValueError as e:
    if os.getenv("ENVIRONMENT") == "production":
        raise

try:
    settings = Settings()
except Exception as e:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError(
            f"Configuration validation failed: {e}\n"
            "Required: DATABASE_URL, SECRET_KEY (min 32 chars). "
            "Production: CORS_ORIGINS (no *), DEBUG=false. See DEPLOY.md."
        ) from e
    import warnings
    warnings.warn(
        f"Settings validation failed: {e}. Using development defaults. Check .env."
    )
    settings = Settings(
        DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/marketplace_db"),
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-" + "x" * 32),
    )

if settings.ENVIRONMENT == "production":
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is required in production.")
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        raise ValueError("SECRET_KEY is required in production and must be at least 32 characters.")
    if settings.DEBUG:
        raise ValueError("DEBUG must be False in production.")
    enforce_production_mail(settings)
    origins = settings.get_cors_origins_list()
    if "*" in origins or not origins:
        raise ValueError("CORS_ORIGINS in production must be a non-empty list of explicit origins. No wildcards.")
