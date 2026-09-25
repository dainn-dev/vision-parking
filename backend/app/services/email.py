"""Outbound email via SMTP (Mailpit locally, real relay in production)."""

import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body_text: str, body_html: str | None = None) -> bool:
    msg = EmailMessage()
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")
    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username or None,
            password=settings.smtp_password or None,
            start_tls=settings.smtp_starttls,
        )
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


async def send_invite_email(to: str, org_name: str, invite_url: str) -> bool:
    return await send_email(
        to,
        f"You're invited to administer {org_name}",
        (
            f"You have been invited to administer {org_name} on "
            f"{settings.platform_name}.\n\nActivate your account: {invite_url}\n"
        ),
    )


async def send_security_alert_email(to: str, alert_type: str, details: str) -> bool:
    return await send_email(
        to,
        f"[Security] {alert_type}",
        f"A security event was detected on {settings.platform_name}.\n\n{details}\n",
    )
