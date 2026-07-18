"""
Startup validation for required configuration.
Ensures application fails fast with clear error messages if misconfigured.
"""
import os
import sys
from app.core.config import settings


def validate_startup_config():
    """
    Validate critical configuration at startup.
    Called during application initialization.
    Raises ValueError with clear error messages if validation fails.
    """
    errors = []
    
    # Check DATABASE_URL
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required but not set")
    elif not settings.DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://")):
        errors.append(
            f"DATABASE_URL must be a PostgreSQL connection string starting with 'postgresql://'\n"
            f"Current value starts with: {settings.DATABASE_URL[:20]}..."
        )
    
    # Check SECRET_KEY
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY is required but not set")
    elif len(settings.SECRET_KEY) < 32:
        errors.append(
            f"SECRET_KEY must be at least 32 characters long\n"
            f"Current length: {len(settings.SECRET_KEY)}\n"
            f"Generate a new key: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )

    # Check DEBUG is False in production
    if getattr(settings, "DEBUG", False):
        errors.append("DEBUG must be False in production. Set DEBUG=false.")

    # If errors found, raise with helpful message
    if errors:
        error_message = (
            "Configuration validation failed:\n\n"
            + "\n".join(f"  • {error}" for error in errors)
            + "\n\n"
            + "Required environment variables:\n"
            + "  • DATABASE_URL: PostgreSQL connection string\n"
            + "  • SECRET_KEY: At least 32 characters (generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\")\n\n"
            + "Note: NO external API keys are required. These are internal configuration values.\n"
            + "See CONFIGURATION.md for complete setup instructions."
        )
        raise ValueError(error_message)
    
    # Log successful validation (only in production to avoid noise in dev)
    if os.getenv("ENVIRONMENT") == "production":
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Configuration validated successfully")


# Validate on module import (for production)
if os.getenv("ENVIRONMENT") == "production":
    validate_startup_config()
