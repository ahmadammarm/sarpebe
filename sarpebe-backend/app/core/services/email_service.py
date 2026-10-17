import asyncio
import logging
import smtplib
from email.message import EmailMessage
from html import escape
from urllib.parse import quote

from app.config import settings

logger = logging.getLogger(__name__)


def _send_smtp(message: EmailMessage) -> None:
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_starttls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password or "")
        server.send_message(message)


async def send_email(to: str, subject: str, text: str, html: str) -> None:
    """
    Sends an email using the configured backend. Never raises: callers run this after the
    HTTP response (BackgroundTasks), where a failure can only be logged. Users can request
    another link through the resend / forgot-password endpoints.
    """
    try:
        if settings.email_backend == "console":
            # Development only: the message (including its one-time link) goes to the log.
            logger.info("EMAIL to=%s subject=%s\n%s", to, subject, text)
            return

        if not settings.smtp_host:
            logger.error("EMAIL_BACKEND=smtp but SMTP_HOST is not set; email to %s not sent", to)
            return

        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text)
        message.add_alternative(html, subtype="html")
        await asyncio.to_thread(_send_smtp, message)
    except Exception:
        logger.exception("Failed to send email to %s", to)


def _frontend_link(path: str, token: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/{path}?token={quote(token)}"


async def send_verification_email(to: str, full_name: str, token: str) -> None:
    link = _frontend_link("verify-email", token)
    hours = settings.verification_token_ttl_hours
    text = (
        f"Halo {full_name},\n\n"
        f"Terima kasih telah mendaftar di SARPEBE. Verifikasi email Anda dengan membuka tautan berikut "
        f"(berlaku {hours} jam):\n\n{link}\n\n"
        "Jika Anda tidak merasa mendaftar, abaikan email ini."
    )
    html = (
        f"<p>Halo {escape(full_name)},</p>"
        "<p>Terima kasih telah mendaftar di SARPEBE. Verifikasi email Anda dengan mengklik tombol di bawah "
        f"(berlaku {hours} jam).</p>"
        f'<p><a href="{escape(link)}">Verifikasi Email</a></p>'
        "<p>Jika Anda tidak merasa mendaftar, abaikan email ini.</p>"
    )
    await send_email(to, "Verifikasi email SARPEBE", text, html)


async def send_password_reset_email(to: str, full_name: str, token: str) -> None:
    link = _frontend_link("reset-password", token)
    minutes = settings.reset_token_ttl_minutes
    text = (
        f"Halo {full_name},\n\n"
        f"Kami menerima permintaan untuk mengatur ulang password akun SARPEBE Anda. Buka tautan berikut "
        f"untuk membuat password baru (berlaku {minutes} menit):\n\n{link}\n\n"
        "Jika Anda tidak meminta ini, abaikan email ini; password Anda tidak berubah."
    )
    html = (
        f"<p>Halo {escape(full_name)},</p>"
        "<p>Kami menerima permintaan untuk mengatur ulang password akun SARPEBE Anda. "
        f"Klik tombol di bawah untuk membuat password baru (berlaku {minutes} menit).</p>"
        f'<p><a href="{escape(link)}">Atur Ulang Password</a></p>'
        "<p>Jika Anda tidak meminta ini, abaikan email ini; password Anda tidak berubah.</p>"
    )
    await send_email(to, "Atur ulang password SARPEBE", text, html)
