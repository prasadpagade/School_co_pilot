"""Stripe payment integration — Checkout sessions, portal, and webhooks."""
import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db, User
from app.auth import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_FAMILY_PRICE_ID = os.getenv("STRIPE_FAMILY_PRICE_ID", "")

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

PLAN_NAMES = {
    STRIPE_PRO_PRICE_ID: "pro",
    STRIPE_FAMILY_PRICE_ID: "family",
}


def _get_stripe():
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe not configured. Set STRIPE_SECRET_KEY in your environment."
        )
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        return stripe
    except ImportError:
        raise HTTPException(status_code=503, detail="stripe package not installed")


@router.get("/plans")
async def list_plans():
    """Return the available pricing plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": "$0",
                "interval": "forever",
                "features": [
                    "1 child, 1 school",
                    "Last 30 days of emails",
                    "10 AI questions per day",
                    "Manual email sync",
                ],
                "cta": "Get Started",
            },
            {
                "id": "pro",
                "name": "Parent Pro",
                "price": "$7.99",
                "interval": "month",
                "stripe_price_id": STRIPE_PRO_PRICE_ID,
                "features": [
                    "1 child, 1 school",
                    "All emails (full history)",
                    "Unlimited AI questions",
                    "Auto calendar sync",
                    "Weekly digest email",
                    "SMS + email alerts",
                ],
                "cta": "Start Free Trial",
                "highlight": True,
            },
            {
                "id": "family",
                "name": "Family",
                "price": "$12.99",
                "interval": "month",
                "stripe_price_id": STRIPE_FAMILY_PRICE_ID,
                "features": [
                    "Up to 3 children + schools",
                    "Everything in Pro",
                    "Family calendar view",
                    "Co-parent sharing",
                ],
                "cta": "Start Free Trial",
            },
        ]
    }


@router.post("/create-checkout")
async def create_checkout_session(
    price_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session and redirect the user to it."""
    if price_id not in (STRIPE_PRO_PRICE_ID, STRIPE_FAMILY_PRICE_ID):
        raise HTTPException(status_code=400, detail="Invalid plan selected.")

    stripe = _get_stripe()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Create or reuse Stripe customer
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, name=user.name)
        user.stripe_customer_id = customer.id
        db.commit()

    try:
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{APP_BASE_URL}/?upgrade=success",
            cancel_url=f"{APP_BASE_URL}/?upgrade=cancelled",
            metadata={"user_id": user_id},
        )
        return {"checkout_url": session.url}
    except Exception as e:
        logger.error(f"Stripe checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal")
async def billing_portal(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Redirect to the Stripe Customer Portal (manage/cancel subscription)."""
    stripe = _get_stripe()
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found.")

    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{APP_BASE_URL}/",
        )
        return {"portal_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe webhook handler — updates subscription status in the database.
    Configure in Stripe dashboard: POST /billing/webhook
    """
    stripe = _get_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        logger.warning(f"Stripe webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")
        subscription_id = data.get("subscription")
        if user_id and subscription_id:
            _activate_subscription(db, user_id, subscription_id, data)

    elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
        _handle_subscription_update(db, stripe, data)

    elif event_type == "customer.subscription.deleted":
        _handle_subscription_cancelled(db, data)

    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(db, stripe, data)

    return JSONResponse({"received": True})


def _activate_subscription(db: Session, user_id: str, subscription_id: str, session_data: dict):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    user.stripe_subscription_id = subscription_id
    user.plan = "pro"  # default; will be refined by subscription.updated event
    db.commit()
    logger.info(f"Subscription activated for user {user_id}")


def _handle_subscription_update(db: Session, stripe, subscription: dict):
    customer_id = subscription.get("customer")
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        return

    status = subscription.get("status")
    if status not in ("active", "trialing"):
        user.plan = "free"
        db.commit()
        return

    # Determine plan from price ID
    price_id = subscription.get("items", {}).get("data", [{}])[0].get("price", {}).get("id", "")
    plan = PLAN_NAMES.get(price_id, "pro")
    user.plan = plan
    user.stripe_subscription_id = subscription.get("id")

    from datetime import datetime
    current_period_end = subscription.get("current_period_end")
    if current_period_end:
        user.subscription_expires_at = datetime.utcfromtimestamp(current_period_end)

    db.commit()
    logger.info(f"Subscription updated for customer {customer_id}: plan={plan}")


def _handle_subscription_cancelled(db: Session, subscription: dict):
    customer_id = subscription.get("customer")
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        user.plan = "free"
        user.stripe_subscription_id = None
        db.commit()
        logger.info(f"Subscription cancelled for customer {customer_id}")


def _handle_payment_failed(db: Session, stripe, invoice: dict):
    customer_id = invoice.get("customer")
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        logger.warning(f"Payment failed for customer {customer_id} ({user.email})")
        # Optionally send notification email here
