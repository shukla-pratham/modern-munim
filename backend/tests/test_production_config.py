"""Production mail settings must fail closed."""
from types import SimpleNamespace

import pytest

from app.core.config import enforce_production_mail


def test_production_requires_smtp_or_resend_and_disables_otp_logs():
    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        enforce_production_mail(SimpleNamespace(
            ENVIRONMENT="production",
            RESEND_API_KEY="",
            SMTP_USER="",
            SMTP_PASSWORD="",
            EMAIL_OTP_DEV_LOG=False,
        ))
    with pytest.raises(ValueError, match="EMAIL_OTP_DEV_LOG"):
        enforce_production_mail(SimpleNamespace(
            ENVIRONMENT="production",
            RESEND_API_KEY="re_1234567890",
            SMTP_USER="",
            SMTP_PASSWORD="",
            EMAIL_OTP_DEV_LOG=True,
        ))
    # Resend valid in production
    enforce_production_mail(SimpleNamespace(
        ENVIRONMENT="production",
        RESEND_API_KEY="re_1234567890",
        SMTP_USER="",
        SMTP_PASSWORD="",
        EMAIL_OTP_DEV_LOG=False,
    ))
    # SMTP valid in production
    enforce_production_mail(SimpleNamespace(
        ENVIRONMENT="production",
        RESEND_API_KEY="",
        SMTP_USER="sender@example.com",
        SMTP_PASSWORD="app-password",
        EMAIL_OTP_DEV_LOG=False,
    ))
    # Dev allows unconfigured
    enforce_production_mail(SimpleNamespace(
        ENVIRONMENT="development",
        RESEND_API_KEY="",
        SMTP_USER="",
        SMTP_PASSWORD="",
        EMAIL_OTP_DEV_LOG=True,
    ))
