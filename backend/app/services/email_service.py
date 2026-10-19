"""SMTP email delivery (Gmail-compatible)."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

import certifi
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(settings.SMTP_USER and settings.SMTP_PASSWORD)


def send_email(to_email: str, subject: str, body: str) -> None:
    if not smtp_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Email is not configured. Set SMTP_USER and SMTP_PASSWORD "
                "(Gmail App Password) in backend/.env, then restart the API."
            ),
        )
    from_addr = (settings.SMTP_FROM or settings.SMTP_USER).strip()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)

    # Keep SMTP attempts short so SPA clients get a real error/fallback quickly.
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=8) as server:
            server.starttls(context=ssl.create_default_context(cafile=certifi.where()))
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not send email: {exc}",
        ) from exc

    logger.info("Sent email to %s subject=%s", to_email, subject)


def _log_dev_otp(to_email: str, code: str, store_name: str | None, reason: str) -> None:
    logger.warning(
        "%s — DEV OTP for %s is %s (store=%s)",
        reason,
        to_email,
        code,
        store_name,
    )


def send_login_otp(to_email: str, code: str, store_name: str | None) -> str:
    """
    Deliver OTP. Returns 'smtp' if emailed, 'log' if written to server logs.
    """
    store_line = f"\nStore: {store_name}\n" if store_name else "\n"
    body = (
        f"Your Modern Munim verification code is: {code}\n"
        f"{store_line}"
        f"This code expires in {settings.EMAIL_OTP_EXPIRE_MINUTES} minutes.\n"
        "If you did not request this, ignore this email.\n"
    )
    if smtp_configured():
        try:
            send_email(to_email, "Your Modern Munim login code", body)
            return "smtp"
        except HTTPException as exc:
            # Development: do not block sign-in when the network blocks SMTP.
            if settings.ENVIRONMENT == "development" and settings.EMAIL_OTP_DEV_LOG:
                _log_dev_otp(
                    to_email,
                    code,
                    store_name,
                    f"SMTP send failed ({exc.detail}); falling back to server log",
                )
                return "log"
            raise

    # Development fallback so local testing works before SMTP is set.
    if settings.ENVIRONMENT == "development" and settings.EMAIL_OTP_DEV_LOG:
        _log_dev_otp(to_email, code, store_name, "SMTP not configured")
        return "log"

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Email is not configured. Set SMTP_USER and SMTP_PASSWORD "
            "(Gmail App Password) in backend/.env, then restart the API."
        ),
    )
