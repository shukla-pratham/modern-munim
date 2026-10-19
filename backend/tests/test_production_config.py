"""Production mail settings must fail closed.

Production requires RESEND_API_KEY (SMTP is not a valid production transport).
Development may run without any email provider configured.
"""
from types import SimpleNamespace

import pytest

from app.core.config import enforce_production_mail


def test_production_requires_resend_api_key():
    """Production must fail when RESEND_API_KEY is absent."""
    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        enforce_production_mail(SimpleNamespace(
            ENVIRONMENT="production",
            RESEND_API_KEY="",
            EMAIL_OTP_DEV_LOG=False,
        ))


def test_production_rejects_smtp_only():
    """SMTP credentials alone are not a valid production transport."""
    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        enforce_production_mail(SimpleNamespace(
            ENVIRONMENT="production",
            RESEND_API_KEY="",
            EMAIL_OTP_DEV_LOG=False,
        ))


def test_production_rejects_otp_dev_log_enabled():
    """OTP dev-log must be disabled in production even when Resend is present."""
    with pytest.raises(ValueError, match="EMAIL_OTP_DEV_LOG"):
        enforce_production_mail(SimpleNamespace(
            ENVIRONMENT="production",
            RESEND_API_KEY="re_1234567890",
            EMAIL_OTP_DEV_LOG=True,
        ))


def test_production_passes_with_resend_and_log_disabled():
    """Valid production config: RESEND_API_KEY set, EMAIL_OTP_DEV_LOG=False."""
    # Must not raise.
    enforce_production_mail(SimpleNamespace(
        ENVIRONMENT="production",
        RESEND_API_KEY="re_1234567890",
        EMAIL_OTP_DEV_LOG=False,
    ))


def test_development_allows_unconfigured():
    """Development environment imposes no mail requirements."""
    # Must not raise even with nothing configured.
    enforce_production_mail(SimpleNamespace(
        ENVIRONMENT="development",
        RESEND_API_KEY="",
        EMAIL_OTP_DEV_LOG=True,
    ))


def test_staging_allows_unconfigured():
    """Non-production environments are not constrained."""
    enforce_production_mail(SimpleNamespace(
        ENVIRONMENT="staging",
        RESEND_API_KEY="",
        EMAIL_OTP_DEV_LOG=True,
    ))
