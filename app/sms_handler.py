"""Twilio SMS chatbot — lets parents ask school questions by text message."""
import base64
import hashlib
import hmac
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import config
from app.database import User, UserSchool, get_db
from app.rag_chat import ask_school_question
from app.auth import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sms", tags=["sms"])


def _validate_twilio_signature(url: str, post_params: dict, signature: str) -> bool:
    """Verify X-Twilio-Signature to prevent spoofed webhook requests."""
    if not config.TWILIO_AUTH_TOKEN:
        return True
    s = url + "".join(k + post_params[k] for k in sorted(post_params))
    mac = hmac.new(config.TWILIO_AUTH_TOKEN.encode(), s.encode(), hashlib.sha1)
    return hmac.compare_digest(base64.b64encode(mac.digest()).decode(), signature)


def _twiml(message: str) -> Response:
    safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>'
    return Response(content=xml, media_type="application/xml")


@router.post("/webhook")
async def sms_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive an inbound SMS from Twilio, answer via RAG, reply with TwiML."""
    form = await request.form()
    from_number = form.get("From", "")
    body = (form.get("Body") or "").strip()

    # Validate Twilio signature
    sig = request.headers.get("X-Twilio-Signature", "")
    if config.TWILIO_AUTH_TOKEN and sig:
        if not _validate_twilio_signature(str(request.url), dict(form), sig):
            logger.warning(f"Rejected spoofed Twilio request from {from_number}")
            return Response(status_code=403)

    if not from_number or not body:
        return _twiml("Sorry, I couldn't understand that message.")

    user = db.query(User).filter(User.phone_number == from_number).first()
    if not user:
        return _twiml(
            "Hi! You're not registered with School Copilot. "
            "Visit the app to sign up and add your phone number."
        )

    school = db.query(UserSchool).filter(UserSchool.user_id == user.id).first()
    store = (school.gemini_store_name if school and school.gemini_store_name
             else config.FILE_SEARCH_STORE_NAME)

    if not store:
        return _twiml(
            "Your school emails haven't been synced yet. "
            "Please complete setup in the app first."
        )

    try:
        answer = ask_school_question(body, store)
        if len(answer) > 1560:
            answer = answer[:1557] + "..."
    except Exception as e:
        logger.error(f"SMS RAG error for user {user.id}: {e}")
        answer = "Sorry, I couldn't find an answer right now. Please try again in a moment."

    logger.info(f"SMS answered for user {user.id} ({from_number})")
    return _twiml(answer)


class SMSRegisterRequest(BaseModel):
    phone_number: str  # E.164 format: +15551234567


@router.post("/register")
async def sms_register(
    body: SMSRegisterRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Save the signed-in user's phone number so they can use SMS."""
    phone = body.phone_number.strip()
    if not phone.startswith("+"):
        raise HTTPException(400, "Phone number must be in E.164 format, e.g. +15551234567")

    conflict = db.query(User).filter(User.phone_number == phone, User.id != user_id).first()
    if conflict:
        raise HTTPException(409, "This phone number is already registered to another account.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.phone_number = phone
    db.commit()

    _send_welcome_sms(phone)
    return {"success": True, "phone_number": phone}


@router.delete("/register")
async def sms_unregister(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove phone number from the current user's account."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.phone_number = None
        db.commit()
    return {"success": True}


def _send_welcome_sms(to: str) -> None:
    if not (config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN and config.TWILIO_PHONE_NUMBER):
        return
    try:
        from twilio.rest import Client
        Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN).messages.create(
            body=(
                "Welcome to School Copilot! "
                "Text this number any time to ask about your child's school. "
                "Try: 'What's happening this week?'"
            ),
            from_=config.TWILIO_PHONE_NUMBER,
            to=to,
        )
    except Exception as e:
        logger.warning(f"Could not send welcome SMS to {to}: {e}")
