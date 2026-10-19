"""Production mail settings must fail closed."""
from types import SimpleNamespace

import pytest

from app.core.config import enforce_production_mail


def test_production_requires_smtp_and_disables_otp_logs():
    with pytest.raises(ValueError, match="SMTP_USER"):
        enforce_production_mail(SimpleNamespace(
            ENVIRONMENT="production",
            SMTP_USER="",
            SMTP_PASSWORD="",
            EMAIL_OTP_DEV_LOG=False,
        ))
    with pytest.raises(ValueError, match="EMAIL_OTP_DEV_LOG"):
        enforce_production_mail(SimpleNamespace(
            ENVIRONMENT="production",
            SMTP_USER="sender@example.com",
            SMTP_PASSWORD="app-password",
            EMAIL_OTP_DEV_LOG=True,
        ))
    enforce_production_mail(SimpleNamespace(
        ENVIRONMENT="development",
        SMTP_USER="",
        SMTP_PASSWORD="",
        EMAIL_OTP_DEV_LOG=True,
    ))
    enforce_production_mail(SimpleNamespace(
        ENVIRONMENT="production",
        SMTP_USER="sender@example.com",
        SMTP_PASSWORD="app-password",
        EMAIL_OTP_DEV_LOG=False,
    ))
