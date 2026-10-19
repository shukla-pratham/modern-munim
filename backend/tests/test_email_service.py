"""Unit tests for email_service.py — mocks all outbound HTTP and SMTP.

These tests exercise routing, error handling, dev-log fallback, and OTP
body formatting without making any real network calls.
"""
from __future__ import annotations

import json
import urllib.error
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import app.services.email_service as svc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_resend_settings(api_key: str = "re_test_key", from_email: str = "onboarding@resend.dev"):
    return SimpleNamespace(
        RESEND_API_KEY=api_key,
        RESEND_FROM_EMAIL=from_email,
        SMTP_USER="",
        SMTP_PASSWORD="",
        SMTP_HOST="smtp.gmail.com",
        SMTP_PORT=587,
        SMTP_FROM="",
        EMAIL_OTP_EXPIRE_MINUTES=10,
        EMAIL_OTP_DEV_LOG=False,
        ENVIRONMENT="production",
    )


def _mock_smtp_settings():
    return SimpleNamespace(
        RESEND_API_KEY="",
        RESEND_FROM_EMAIL="",
        SMTP_USER="dev@example.com",
        SMTP_PASSWORD="app-password",
        SMTP_HOST="smtp.gmail.com",
        SMTP_PORT=587,
        SMTP_FROM="",
        EMAIL_OTP_EXPIRE_MINUTES=10,
        EMAIL_OTP_DEV_LOG=True,
        ENVIRONMENT="development",
    )


def _make_http_response(status_code: int = 200, body: bytes = b'{"id":"abc"}'):
    """Minimal urllib response mock."""
    mock_resp = MagicMock()
    mock_resp.status = status_code
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# send_via_resend
# ---------------------------------------------------------------------------

class TestSendViaResend:
    def test_happy_path_calls_resend_api(self):
        """A successful 200 response should not raise."""
        mock_resp = _make_http_response(200)
        with patch("app.services.email_service.settings", _mock_resend_settings()):
            with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
                svc.send_via_resend("user@example.com", "Subject", "Body text")
                mock_open.assert_called_once()
                call_args = mock_open.call_args
                req = call_args[0][0]
                assert req.full_url == "https://api.resend.com/emails"
                assert req.get_header("Content-type") == "application/json"
                assert req.get_header("Authorization") == "Bearer re_test_key"
                payload = json.loads(req.data.decode())
                assert payload["to"] == ["user@example.com"]
                assert payload["subject"] == "Subject"
                assert payload["from"] == "onboarding@resend.dev"

    def test_uses_resend_from_email_setting(self):
        """RESEND_FROM_EMAIL setting is forwarded in the payload."""
        mock_resp = _make_http_response(200)
        settings = _mock_resend_settings(from_email="noreply@mystore.com")
        with patch("app.services.email_service.settings", settings):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                svc.send_via_resend("x@example.com", "S", "B")

    def test_http_error_raises_502(self):
        """A non-2xx HTTP response from Resend must raise HTTP 502."""
        exc = urllib.error.HTTPError(
            url="https://api.resend.com/emails",
            code=422,
            msg="Unprocessable Entity",
            hdrs=None,  # type: ignore[arg-type]
            fp=BytesIO(b'{"message":"invalid from address"}'),
        )
        with patch("app.services.email_service.settings", _mock_resend_settings()):
            with patch("urllib.request.urlopen", side_effect=exc):
                with pytest.raises(HTTPException) as exc_info:
                    svc.send_via_resend("user@example.com", "S", "B")
                assert exc_info.value.status_code == 502
                assert "422" in exc_info.value.detail

    def test_connection_error_raises_502(self):
        """A network failure must raise HTTP 502."""
        with patch("app.services.email_service.settings", _mock_resend_settings()):
            with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
                with pytest.raises(HTTPException) as exc_info:
                    svc.send_via_resend("user@example.com", "S", "B")
                assert exc_info.value.status_code == 502


# ---------------------------------------------------------------------------
# send_email routing
# ---------------------------------------------------------------------------

class TestSendEmailRouting:
    def test_prefers_resend_when_api_key_set(self):
        """Resend is the primary transport when RESEND_API_KEY is present."""
        settings = _mock_resend_settings()
        with patch("app.services.email_service.settings", settings):
            with patch.object(svc, "send_via_resend") as mock_resend:
                result = svc.send_email("a@b.com", "S", "B")
                mock_resend.assert_called_once_with("a@b.com", "S", "B")
                assert result == "resend"

    def test_falls_back_to_smtp_when_no_resend_key(self):
        """SMTP is used when RESEND_API_KEY is absent and SMTP creds are set."""
        settings = _mock_smtp_settings()
        with patch("app.services.email_service.settings", settings):
            with patch.object(svc, "_send_via_smtp") as mock_smtp:
                result = svc.send_email("a@b.com", "S", "B")
                mock_smtp.assert_called_once_with("a@b.com", "S", "B")
                assert result == "smtp"

    def test_raises_503_when_neither_configured(self):
        """No provider configured → 503 Service Unavailable."""
        settings = SimpleNamespace(
            RESEND_API_KEY="",
            RESEND_FROM_EMAIL="",
            SMTP_USER="",
            SMTP_PASSWORD="",
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_FROM="",
        )
        with patch("app.services.email_service.settings", settings):
            with pytest.raises(HTTPException) as exc_info:
                svc.send_email("a@b.com", "S", "B")
            assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# send_login_otp
# ---------------------------------------------------------------------------

class TestSendLoginOtp:
    def test_returns_resend_when_api_key_configured(self):
        """Returns 'resend' delivery mode when Resend API key is set."""
        settings = _mock_resend_settings()
        with patch("app.services.email_service.settings", settings):
            with patch.object(svc, "send_via_resend"):
                result = svc.send_login_otp("user@example.com", "123456", "My Store")
                assert result == "resend"

    def test_otp_body_contains_code_and_store(self):
        """OTP body text must include the code, store name, and expiry."""
        settings = _mock_resend_settings()
        captured = {}

        def capture(to, subject, body):
            captured["body"] = body

        with patch("app.services.email_service.settings", settings):
            with patch.object(svc, "send_via_resend", side_effect=capture):
                svc.send_login_otp("x@example.com", "482913", "Sunrise Bakery")
                assert "482913" in captured["body"]
                assert "Sunrise Bakery" in captured["body"]
                assert "10 minutes" in captured["body"]

    def test_otp_body_without_store_name(self):
        """send_login_otp works correctly when store_name is None."""
        settings = _mock_resend_settings()
        with patch("app.services.email_service.settings", settings):
            with patch.object(svc, "send_via_resend") as mock_resend:
                result = svc.send_login_otp("x@example.com", "000001", None)
                assert result == "resend"
                _, _, body = mock_resend.call_args[0]
                assert "None" not in body

    def test_dev_log_fallback_when_resend_fails_in_dev(self):
        """In development, a failed Resend call falls back to server log."""
        dev_settings = SimpleNamespace(
            RESEND_API_KEY="re_test",
            RESEND_FROM_EMAIL="onboarding@resend.dev",
            SMTP_USER="",
            SMTP_PASSWORD="",
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_FROM="",
            EMAIL_OTP_EXPIRE_MINUTES=10,
            EMAIL_OTP_DEV_LOG=True,
            ENVIRONMENT="development",
        )
        with patch("app.services.email_service.settings", dev_settings):
            with patch.object(svc, "send_via_resend", side_effect=HTTPException(status_code=502, detail="network error")):
                result = svc.send_login_otp("x@example.com", "111111", None)
                assert result == "log"

    def test_no_dev_log_fallback_in_production(self):
        """In production, a Resend failure must propagate — no silent log fallback."""
        prod_settings = _mock_resend_settings()
        prod_settings = SimpleNamespace(**{**prod_settings.__dict__, "ENVIRONMENT": "production", "EMAIL_OTP_DEV_LOG": False})
        with patch("app.services.email_service.settings", prod_settings):
            with patch.object(svc, "send_via_resend", side_effect=HTTPException(status_code=502, detail="network error")):
                with pytest.raises(HTTPException) as exc_info:
                    svc.send_login_otp("x@example.com", "111111", None)
                assert exc_info.value.status_code == 502

    def test_raises_503_in_production_with_no_provider(self):
        """503 raised in production when no email provider is configured."""
        unconfigured = SimpleNamespace(
            RESEND_API_KEY="",
            RESEND_FROM_EMAIL="",
            SMTP_USER="",
            SMTP_PASSWORD="",
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_FROM="",
            EMAIL_OTP_EXPIRE_MINUTES=10,
            EMAIL_OTP_DEV_LOG=False,
            ENVIRONMENT="production",
        )
        with patch("app.services.email_service.settings", unconfigured):
            with pytest.raises(HTTPException) as exc_info:
                svc.send_login_otp("x@example.com", "111111", None)
            assert exc_info.value.status_code == 503

    def test_dev_log_fallback_when_no_provider_configured(self):
        """In development with EMAIL_OTP_DEV_LOG=True, 'log' is returned when no provider exists."""
        dev_no_provider = SimpleNamespace(
            RESEND_API_KEY="",
            RESEND_FROM_EMAIL="",
            SMTP_USER="",
            SMTP_PASSWORD="",
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_FROM="",
            EMAIL_OTP_EXPIRE_MINUTES=10,
            EMAIL_OTP_DEV_LOG=True,
            ENVIRONMENT="development",
        )
        with patch("app.services.email_service.settings", dev_no_provider):
            result = svc.send_login_otp("x@example.com", "999999", "Test Shop")
            assert result == "log"
