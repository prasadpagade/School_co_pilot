"""Per-user data path helpers and isolation utilities."""
import os
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.database import User, UserSchool

# Base directory for all per-user data
DATA_ROOT = Path(os.getenv("DATA_ROOT", "data/users"))


def user_dir(user_id: str) -> Path:
    """Return (and create) the root data directory for a user."""
    path = DATA_ROOT / user_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_raw_emails_dir(user_id: str) -> Path:
    p = user_dir(user_id) / "raw_emails"
    p.mkdir(exist_ok=True)
    return p


def user_attachments_dir(user_id: str) -> Path:
    p = user_dir(user_id) / "attachments"
    p.mkdir(exist_ok=True)
    return p


def user_consolidated_dir(user_id: str) -> Path:
    p = user_dir(user_id) / "consolidated"
    p.mkdir(exist_ok=True)
    return p


def user_gmail_token_path(user_id: str) -> str:
    return str(user_dir(user_id) / "gmail_token.json")


def user_calendar_token_path(user_id: str) -> str:
    return str(user_dir(user_id) / "calendar_token.pickle")


def user_rag_cache_path(user_id: str) -> str:
    return str(user_dir(user_id) / ".rag_cache.json")


# ── DB helpers ───────────────────────────────────────────────────────────────

def get_or_create_user(db: Session, google_id: str, email: str, name: str, picture: Optional[str] = None) -> User:
    """Upsert a user record on login."""
    from datetime import datetime
    user = db.query(User).filter(User.id == google_id).first()
    if user:
        user.last_login = datetime.utcnow()
        user.name = name
        user.picture = picture
    else:
        user = User(id=google_id, email=email, name=name, picture=picture)
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_school(db: Session, user_id: str) -> Optional[UserSchool]:
    return db.query(UserSchool).filter(UserSchool.user_id == user_id).first()


def save_user_school(
    db: Session,
    user_id: str,
    school_domains: str,
    school_senders: str,
    child_name: Optional[str] = None,
    school_name: Optional[str] = None,
) -> UserSchool:
    """Save (or update) a user's school configuration."""
    school = db.query(UserSchool).filter(UserSchool.user_id == user_id).first()
    if not school:
        school = UserSchool(
            user_id=user_id,
            gmail_token_path=user_gmail_token_path(user_id),
            calendar_token_path=user_calendar_token_path(user_id),
        )
        db.add(school)

    school.school_domains = school_domains
    school.school_senders = school_senders

    # Update personalization on the User row
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if child_name:
            user.child_name = child_name
        if school_name:
            user.school_name = school_name
        user.onboarding_complete = True

    db.commit()
    db.refresh(school)
    return school


def check_daily_quota(db: Session, user_id: str, limit: int) -> bool:
    """
    Return True if the user is within their daily question quota.
    Resets the counter at midnight.
    """
    from datetime import date
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    today = date.today().isoformat()
    if user.daily_questions_date != today:
        # New day — reset counter
        user.daily_questions = 0
        user.daily_questions_date = today
        db.commit()

    return user.daily_questions < limit


def increment_daily_questions(db: Session, user_id: str) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.daily_questions = (user.daily_questions or 0) + 1
        db.commit()


PLAN_LIMITS = {
    "free": 10,
    "pro": 9999,
    "family": 9999,
}


def get_daily_limit(plan: str) -> int:
    return PLAN_LIMITS.get(plan, 10)
