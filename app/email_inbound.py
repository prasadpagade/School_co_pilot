"""Postmark inbound email webhook — universal email forwarding for non-Gmail support.

Setup:
1. Sign up at postmarkapp.com, create an Inbound Server
2. Point MX record for INBOUND_EMAIL_DOMAIN to Postmark's servers
3. Set Inbound Webhook URL to https://yourapp.com/email/inbound
4. Copy the inbound token to POSTMARK_INBOUND_TOKEN in .env

Each user gets a unique forwarding address (abc123@mail.schoolcopilot.app) generated
during onboarding. They add a filter in their email client to forward school emails there.
"""
import base64
import logging
import re
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import config
from app.database import SessionLocal, UserSchool
from app.user_store import user_attachments_dir, user_raw_emails_dir

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/email", tags=["email"])


def _slugify(text: str, max_len: int = 50) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "_", text).strip("_")
    return text[:max_len] or "email"


def _strip_html(html: str) -> str:
    if not html:
        return ""
    clean = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", clean).strip()


@router.post("/inbound")
async def email_inbound(request: Request):
    """
    Receive a forwarded school email from Postmark, save it to the user's
    raw_emails directory so the existing RAG pipeline can pick it up.
    """
    token = request.headers.get("X-Postmark-Inbound-Token", "")
    if config.POSTMARK_INBOUND_TOKEN and token != config.POSTMARK_INBOUND_TOKEN:
        logger.warning("Rejected inbound email with invalid Postmark token")
        raise HTTPException(403, "Invalid inbound token")

    data = await request.json()

    # Resolve destination address
    to_list = data.get("ToFull") or []
    if isinstance(to_list, list) and to_list:
        to_address = to_list[0].get("Email", "").lower()
    else:
        to_address = str(data.get("OriginalRecipient", "")).lower()

    if not to_address:
        return {"ignored": True, "reason": "no destination address"}

    # Find which user owns this forwarding address
    with SessionLocal() as db:
        school = db.query(UserSchool).filter(
            UserSchool.forwarding_address == to_address
        ).first()
        if not school:
            logger.info(f"No user registered for forwarding address: {to_address}")
            return {"ignored": True, "reason": "unknown recipient"}
        user_id = school.user_id

    subject = (data.get("Subject") or "No Subject").strip()
    sender = data.get("From", "unknown")
    date_str = data.get("Date", datetime.utcnow().isoformat())
    body = data.get("TextBody") or _strip_html(data.get("HtmlBody", ""))

    # Save email as a .txt file matching the existing pipeline format
    try:
        date_prefix = datetime.fromisoformat(date_str[:10]).strftime("%Y-%m-%d")
    except Exception:
        date_prefix = datetime.utcnow().strftime("%Y-%m-%d")

    raw_dir = user_raw_emails_dir(user_id)
    base_name = f"{date_prefix}_{_slugify(subject)}"
    dest = raw_dir / f"{base_name}.txt"
    counter = 1
    while dest.exists():
        dest = raw_dir / f"{base_name}_{counter}.txt"
        counter += 1

    content = f"From: {sender}\nDate: {date_str}\nSubject: {subject}\n\n{body}"
    dest.write_text(content, encoding="utf-8")
    logger.info(f"Saved forwarded email for user {user_id}: {dest.name}")

    # Save attachments
    attach_dir = user_attachments_dir(user_id)
    saved = []
    for att in data.get("Attachments", []):
        name = att.get("Name", "attachment")
        raw_b64 = att.get("Content", "")
        if not raw_b64:
            continue
        try:
            (attach_dir / name).write_bytes(base64.b64decode(raw_b64))
            saved.append(name)
        except Exception as e:
            logger.warning(f"Could not save attachment '{name}': {e}")

    # Update last_ingested_at
    with SessionLocal() as db:
        s = db.query(UserSchool).filter(UserSchool.user_id == user_id).first()
        if s:
            s.last_ingested_at = datetime.utcnow()
            db.commit()

    return {"processed": True, "subject": subject, "attachments": saved}
