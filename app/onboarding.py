"""Onboarding wizard API endpoints — guides new parents through setup."""
import logging
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import config
from app.database import get_db
from app.auth import get_current_user_id
from app.user_store import (
    get_user_school, save_user_school, get_or_create_user,
    user_gmail_token_path, user_consolidated_dir
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingSetupRequest(BaseModel):
    school_domains: str    # e.g. "@lincoln.edu,@pta.lincoln.edu"
    school_senders: str    # e.g. "principal@lincoln.edu,newsletter@lincoln.edu"
    child_name: Optional[str] = None
    school_name: Optional[str] = None


class OnboardingStatusResponse(BaseModel):
    complete: bool
    steps: dict
    child_name: str
    school_name: str
    plan: str
    forwarding_address: Optional[str] = None


@router.get("/status", response_model=OnboardingStatusResponse)
async def onboarding_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return which onboarding steps are complete for the current user."""
    from app.database import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    school = get_user_school(db, user_id)

    steps = {
        "google_login": True,                               # They're here — step 1 done
        "school_configured": bool(school and (school.school_domains or school.school_senders)),
        "gmail_connected": bool(school and school.gmail_token_path),
        "first_ingestion": bool(school and school.last_ingested_at),
    }

    return OnboardingStatusResponse(
        complete=user.onboarding_complete,
        steps=steps,
        child_name=user.child_name or "your child",
        school_name=user.school_name or "school",
        plan=user.plan or "free",
        forwarding_address=school.forwarding_address if school else None,
    )


@router.post("/setup")
async def onboarding_setup(
    request_body: OnboardingSetupRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Save the user's school configuration (step 2 of onboarding).
    Triggers first email ingestion in the background.
    """
    # Validate at least one filter is provided
    if not request_body.school_domains.strip() and not request_body.school_senders.strip():
        raise HTTPException(
            status_code=400,
            detail="Provide at least one school email domain or specific sender address."
        )

    school = save_user_school(
        db=db,
        user_id=user_id,
        school_domains=request_body.school_domains.strip(),
        school_senders=request_body.school_senders.strip(),
        child_name=request_body.child_name,
        school_name=request_body.school_name,
    )

    # Generate a unique forwarding address if not yet assigned
    if not school.forwarding_address:
        token = secrets.token_hex(8)
        school.forwarding_address = f"{token}@{config.INBOUND_EMAIL_DOMAIN}"
        db.commit()
        db.refresh(school)

    logger.info(f"Onboarding setup saved for user {user_id}")

    return {
        "success": True,
        "message": "School configuration saved. Starting email sync...",
        "forwarding_address": school.forwarding_address,
        "forwarding_instructions": (
            f"Forward school emails to {school.forwarding_address}. "
            "In Gmail/Outlook: Settings → Filters → Forward emails from @yourschool.edu to this address."
        ),
    }


@router.post("/trigger-first-sync")
async def trigger_first_sync(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Kick off the first email ingestion for a newly onboarded user."""
    school = get_user_school(db, user_id)
    if not school:
        raise HTTPException(status_code=400, detail="Complete school setup first.")

    def run_ingestion():
        try:
            import subprocess, sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            script_path = project_root / "scripts" / "backfill_emails.py"
            subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=300,
            )
            # Mark ingestion time
            from datetime import datetime
            from app.database import SessionLocal
            with SessionLocal() as session:
                s = session.query(type(school)).filter_by(id=school.id).first()
                if s:
                    s.last_ingested_at = datetime.utcnow()
                    session.commit()
        except Exception as e:
            logger.error(f"First sync failed for {user_id}: {e}")

    background_tasks.add_task(run_ingestion)
    return {"success": True, "message": "Email sync started. This may take a few minutes."}
