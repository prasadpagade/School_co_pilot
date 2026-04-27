"""SQLAlchemy models and database setup (SQLite for beta, PostgreSQL for production)."""
import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Boolean,
    DateTime, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.engine import Engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/school_copilot.db")

# SQLite-specific: enable WAL mode for concurrent reads
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine: Engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)           # Google sub (unique per Google account)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String)                         # Google profile picture URL
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    # Personalization
    child_name = Column(String, default="your child")
    school_name = Column(String, default="school")

    # Subscription
    plan = Column(String, default="free")            # "free", "pro", "family"
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    subscription_expires_at = Column(DateTime)

    # Daily usage counter (reset each day)
    daily_questions = Column(Integer, default=0)
    daily_questions_date = Column(String)            # YYYY-MM-DD — when counter was last reset

    # Setup state
    onboarding_complete = Column(Boolean, default=False)

    # SMS access
    phone_number = Column(String, unique=True)       # E.164 format, e.g. +15551234567


class UserSchool(Base):
    """School connection for a user — email domains and senders to ingest."""
    __tablename__ = "user_schools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    school_domains = Column(Text, default="")        # comma-separated
    school_senders = Column(Text, default="")        # comma-separated
    gmail_token_path = Column(String)                # path to per-user token file
    calendar_token_path = Column(String)
    gemini_store_name = Column(String)               # per-user Gemini file store
    forwarding_address = Column(String, unique=True) # inbound email address for non-Gmail
    created_at = Column(DateTime, default=datetime.utcnow)
    last_ingested_at = Column(DateTime)


class EmailIngestionLog(Base):
    """Audit trail of every ingestion run."""
    __tablename__ = "email_ingestion_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    ran_at = Column(DateTime, default=datetime.utcnow)
    emails_ingested = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)


def create_tables() -> None:
    """Create all tables (idempotent — safe to call on every startup)."""
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
