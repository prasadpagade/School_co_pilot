"""Per-user daily question quota enforcement."""
import logging
from typing import Optional

from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.database import get_db, User
from app.auth import get_current_user_id_optional
from app.user_store import check_daily_quota, increment_daily_questions, get_daily_limit

logger = logging.getLogger(__name__)

FREE_DAILY_LIMIT = 10

UPGRADE_MESSAGE = (
    "You've reached your daily limit of 10 questions on the free plan. "
    "Upgrade to Parent Pro ($7.99/month) for unlimited questions. "
    "Visit /billing/plans to see all options."
)


def enforce_quota(request: Request, db: Session = Depends(get_db)) -> Optional[str]:
    """
    FastAPI dependency — checks daily quota for authenticated users.
    Returns the user_id if quota is OK, or None for unauthenticated (single-user mode).
    Raises HTTP 429 if the quota is exceeded.
    """
    user_id = get_current_user_id_optional(request)
    if not user_id:
        # Single-user / unauthenticated mode — no quota enforcement
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    limit = get_daily_limit(user.plan or "free")
    if not check_daily_quota(db, user_id, limit):
        raise HTTPException(
            status_code=429,
            detail=UPGRADE_MESSAGE,
            headers={"X-Upgrade-URL": "/billing/plans"},
        )

    return user_id


def record_question_usage(user_id: Optional[str], db: Session) -> None:
    """Increment the user's daily question counter after a successful chat response."""
    if user_id:
        try:
            increment_daily_questions(db, user_id)
        except Exception as e:
            logger.warning(f"Failed to increment usage counter for {user_id}: {e}")


def get_usage_status(user_id: str, db: Session) -> dict:
    """Return the current usage stats for display in the UI."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}

    from datetime import date
    today = date.today().isoformat()
    if user.daily_questions_date != today:
        used = 0
    else:
        used = user.daily_questions or 0

    plan = user.plan or "free"
    limit = get_daily_limit(plan)

    return {
        "plan": plan,
        "daily_limit": limit,
        "questions_used_today": used,
        "questions_remaining": max(0, limit - used),
        "is_unlimited": limit >= 9999,
    }
