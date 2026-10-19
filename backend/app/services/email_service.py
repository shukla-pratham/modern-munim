"""Transactional email delivery via Resend HTTPS REST API.

Production: Resend HTTPS API (RESEND_API_KEY required).
Development: Falls back to SMTP when configured, or logs OTP to server console
             when EMAIL_OTP_DEV_LOG=true (default in dev, disabled in production).
"""
from __future__ import annotations

import json
import logging
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage

import certifi
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Transport helpers
# ---------------------------------------------------------------------------


def resend_configured() -> bool:
    """Return True when a Resend API key is present and non-empty."""
    return bool(settings.RESEND_API_KEY and settings.RESEND_API_KEY.strip())


def smtp_configured() -> bool:
    """Return True when SMTP credentials are present (dev fallback only)."""
    return bool(settings.SMTP_USER and settings.SMTP_PASSWORD)


def send_via_resend(to_email: str, subject: str, body: str) -> None:
    """Send transactional email via the Resend HTTPS REST API.

    Immune to SMTP port blocks on cloud hosting.  Uses stdlib only — no
    third-party ``resend`` SDK required.
    """
    api_key = settings.RESEND_API_KEY.strip()
    from_email = (settings.RESEND_FROM_EMAIL or "onboarding@resend.dev").strip()
    payload = json.dumps(
        {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ModernMunim/2.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
            logger.info(
                "Resend API response for %s: status=%d", to_email, resp.status
            )
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        logger.error("Resend API failed (%d): %s", exc.code, err_body)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not send email via Resend: HTTP {exc.code} — {err_body}",
        ) from exc
    except Exception as exc:
        logger.error(
            "Resend API request exception for %s: %s", to_email, exc, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not connect to Resend API: {exc}",
        ) from exc


def _send_via_smtp(to_email: str, subject: str, body: str) -> None:
    """Dev-only SMTP fallback.  Not used in production."""
    from_addr = (settings.SMTP_FROM or settings.SMTP_USER).strip()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=8) as server:
            server.starttls(context=ssl.create_default_context(cafile=certifi.where()))
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            logger.info("Sent email to %s via SMTP subject=%s", to_email, subject)
    except Exception as exc:
        logger.error(
            "Failed to send email to %s via SMTP: %s", to_email, exc, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not send email via SMTP: {exc}",
        ) from exc


def send_email(to_email: str, subject: str, body: str) -> str:
    """Deliver a transactional email.

    Priority:
      1. Resend HTTPS API (production + dev when RESEND_API_KEY is set)
      2. SMTP (dev convenience fallback when SMTP credentials are set)
      3. Raise 503 if neither is configured

    Returns a string delivery-mode label: ``"resend"`` | ``"smtp"``.
    """
    if resend_configured():
        send_via_resend(to_email, subject, body)
        return "resend"

    if smtp_configured():
        _send_via_smtp(to_email, subject, body)
        return "smtp"

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Email is not configured. "
            "Set RESEND_API_KEY (required in production) "
            "or SMTP_USER/SMTP_PASSWORD (development only)."
        ),
    )


# ---------------------------------------------------------------------------
# OTP helpers
# ---------------------------------------------------------------------------


def _log_dev_otp(to_email: str, code: str, store_name: str | None, reason: str) -> None:
    logger.warning(
        "%s — DEV OTP for %s is %s (store=%s)",
        reason,
        to_email,
        code,
        store_name,
    )


def send_login_otp(to_email: str, code: str, store_name: str | None) -> str:
    """Deliver a login OTP to *to_email*.

    Returns the delivery mode:
      ``"resend"``  — sent via Resend HTTPS API
      ``"smtp"``    — sent via SMTP (dev fallback)
      ``"log"``     — written to server logs (development only, EMAIL_OTP_DEV_LOG=true)

    In production Resend is required; the dev-log fallback is explicitly
    disabled (EMAIL_OTP_DEV_LOG=false enforced by config.enforce_production_mail).
    """
    store_line = f"\nStore: {store_name}\n" if store_name else "\n"
    body = (
        f"Your Modern Munim verification code is: {code}\n"
        f"{store_line}"
        f"This code expires in {settings.EMAIL_OTP_EXPIRE_MINUTES} minutes.\n"
        f"If you did not request this, ignore this email.\n"
    )

    if resend_configured() or smtp_configured():
        try:
            return send_email(to_email, "Your Modern Munim login code", body)
        except HTTPException as exc:
            # In development, do not block sign-in when local network blocks delivery.
            if settings.ENVIRONMENT == "development" and settings.EMAIL_OTP_DEV_LOG:
                _log_dev_otp(
                    to_email,
                    code,
                    store_name,
                    f"Email send failed ({exc.detail}); falling back to server log",
                )
                return "log"
            raise

    # Development fallback when no email provider is configured at all.
    if settings.ENVIRONMENT == "development" and settings.EMAIL_OTP_DEV_LOG:
        _log_dev_otp(to_email, code, store_name, "Email service not configured")
        return "log"

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Email service is not configured. "
            "Set RESEND_API_KEY (required in production) "
            "or SMTP_USER/SMTP_PASSWORD (development only)."
        ),
    )
