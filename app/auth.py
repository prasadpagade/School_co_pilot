"""Google OAuth2 web login + JWT session tokens."""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

# ── JWT ─────────────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30


def _create_access_token(user_id: str, email: str) -> str:
    try:
        from jose import jwt
    except ImportError:
        raise RuntimeError("python-jose not installed — run: pip install python-jose[cryptography]")

    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "email": email, "exp": expire},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def _decode_token(token: str) -> Optional[dict]:
    try:
        from jose import jwt, JWTError
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def get_current_user_id(request: Request) -> str:
    """
    FastAPI dependency — extracts the authenticated user_id from the session cookie.
    Raises 401 if not authenticated.
    """
    token = request.cookies.get("session_token")
    if not token:
        # Also accept Bearer header for API clients
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = _decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return payload["sub"]


def get_current_user_id_optional(request: Request) -> Optional[str]:
    """Same as get_current_user_id but returns None instead of raising."""
    try:
        return get_current_user_id(request)
    except HTTPException:
        return None


# ── Google OAuth2 ────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback")

# Scopes: identity + Gmail read + Calendar write
OAUTH_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]


def get_google_oauth_url(state: Optional[str] = None) -> str:
    """Build the Google OAuth consent URL."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID not configured. See .env.example for setup instructions."
        )
    try:
        from authlib.integrations.requests_client import OAuth2Session
    except ImportError:
        raise RuntimeError("authlib not installed — run: pip install authlib")

    client = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        redirect_uri=OAUTH_REDIRECT_URI,
        scope=" ".join(OAUTH_SCOPES),
    )
    url, _ = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        state=state or str(uuid.uuid4()),
        access_type="offline",   # request refresh_token
        prompt="consent",        # always show consent to get refresh_token
    )
    return url


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    try:
        from authlib.integrations.requests_client import OAuth2Session
    except ImportError:
        raise RuntimeError("authlib not installed")

    client = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=OAUTH_REDIRECT_URI,
    )
    token = client.fetch_token(
        "https://oauth2.googleapis.com/token",
        code=code,
    )
    return token


def get_google_user_info(access_token: str) -> dict:
    """Fetch the authenticated user's Google profile."""
    import requests
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def create_session_response(user_id: str, email: str, redirect_url: str = "/") -> RedirectResponse:
    """Create a redirect response with the session cookie set."""
    token = _create_access_token(user_id, email)
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * JWT_EXPIRE_DAYS,
    )
    return response
