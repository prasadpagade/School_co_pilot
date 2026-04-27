"""Email notification sender using Resend (free tier: 3,000 emails/month)."""
import logging
from typing import Optional
from app.config import config

logger = logging.getLogger(__name__)


def send_new_email_alert(new_count: int, email_subjects: Optional[list] = None) -> bool:
    """
    Send an email notification when new school emails are detected.

    Returns True if sent successfully, False otherwise.
    """
    if not config.RESEND_API_KEY or not config.PARENT_EMAIL:
        logger.debug("Notifications not configured (RESEND_API_KEY or PARENT_EMAIL missing) — skipping")
        return False

    try:
        import resend
        resend.api_key = config.RESEND_API_KEY

        subject_list_html = ""
        if email_subjects:
            items = "".join(f"<li>{s}</li>" for s in email_subjects[:5])
            subject_list_html = f"<ul>{items}</ul>"
            if len(email_subjects) > 5:
                subject_list_html += f"<p>...and {len(email_subjects) - 5} more.</p>"

        body_html = f"""
        <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
            <h2 style="color: #667eea; margin-bottom: 8px;">📧 {new_count} New School Email{"s" if new_count != 1 else ""}</h2>
            <p style="color: #555;">New messages arrived from <strong>{config.SCHOOL_NAME}</strong>.</p>
            {subject_list_html}
            <a href="#" style="display:inline-block;margin-top:16px;padding:12px 24px;background:#667eea;color:white;border-radius:8px;text-decoration:none;font-weight:600;">
                Open School Copilot
            </a>
            <p style="margin-top:24px;font-size:12px;color:#999;">
                You're receiving this because you set up School Copilot notifications.
            </p>
        </div>
        """

        resend.Emails.send({
            "from": config.NOTIFICATION_FROM_EMAIL,
            "to": [config.PARENT_EMAIL],
            "subject": f"📧 {new_count} new email{'s' if new_count != 1 else ''} from {config.SCHOOL_NAME}",
            "html": body_html,
        })

        logger.info(f"Notification sent to {config.PARENT_EMAIL} for {new_count} new email(s)")
        return True

    except ImportError:
        logger.warning("resend package not installed — run: pip install resend")
        return False
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False


def send_weekly_digest(digest_html: str, subject: str) -> bool:
    """Send a weekly school digest email."""
    if not config.RESEND_API_KEY or not config.PARENT_EMAIL:
        logger.debug("Notifications not configured — skipping digest")
        return False

    try:
        import resend
        resend.api_key = config.RESEND_API_KEY

        resend.Emails.send({
            "from": config.NOTIFICATION_FROM_EMAIL,
            "to": [config.PARENT_EMAIL],
            "subject": subject,
            "html": digest_html,
        })

        logger.info(f"Weekly digest sent to {config.PARENT_EMAIL}")
        return True

    except Exception as e:
        logger.error(f"Failed to send weekly digest: {e}")
        return False
