"""Weekly school digest email — sent every Sunday morning.

This is the highest-viral-potential feature: parents forward it to their spouse,
other parents ask "how did you get this?" → word-of-mouth growth.
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.config import config

logger = logging.getLogger(__name__)


def _generate_digest_content(child_name: str, school_name: str) -> Optional[str]:
    """Use Gemini to summarize the week's school emails into a digest."""
    if not config.GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set — cannot generate digest")
        return None

    consolidated_dir = Path(config.CONSOLIDATED_DIR)
    if not consolidated_dir.exists():
        return None

    md_files = sorted(
        consolidated_dir.glob("school-data-*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not md_files:
        return None

    try:
        content = md_files[0].read_text(encoding="utf-8")[:15000]  # cap at ~15k chars
    except Exception as e:
        logger.error(f"Failed to read consolidated file: {e}")
        return None

    try:
        import google.genai as genai
        from google.genai import types

        client = genai.Client(api_key=config.GOOGLE_API_KEY)
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).strftime("%B %d")
        week_end = (now - timedelta(days=now.weekday()) + timedelta(days=6)).strftime("%B %d, %Y")

        prompt = f"""You are creating a friendly weekly school digest email for a parent.
Child: {child_name} | School: {school_name}
Week: {week_start} – {week_end}

Based on the school emails below, create a concise, friendly digest with these sections:
1. **This Week at a Glance** — 2-3 bullet points of the most important things happening
2. **Upcoming Events** — list events with dates in the next 2 weeks
3. **Action Items** — things the parent needs to do (sign forms, bring items, RSVP, etc.)
4. **Good to Know** — any school news, announcements, or reminders

Keep it friendly, scannable, and under 300 words. Use emojis sparingly for visual clarity.
If there is nothing relevant for a section, skip it.

School emails:
{content}

Generate the digest now:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[types.Part.from_text(text=prompt)],
        )
        return response.text if hasattr(response, "text") else None

    except Exception as e:
        logger.error(f"Gemini digest generation failed: {e}")
        return None


def _render_digest_html(digest_text: str, child_name: str, school_name: str, week_label: str) -> str:
    """Wrap the digest text in a clean HTML email template."""
    # Convert simple markdown to HTML
    lines = digest_text.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("**") and line.endswith("**"):
            html_lines.append(f"<h3>{line[2:-2]}</h3>")
        elif line.startswith("- ") or line.startswith("• "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p>{line}</p>")
    body_html = "\n".join(html_lines)

    return f"""
    <div style="font-family: -apple-system, 'Helvetica Neue', sans-serif; max-width: 560px; margin: 0 auto; padding: 0;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 28px 32px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 22px;">📘 School Copilot</h1>
            <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0; font-size: 14px;">
                Weekly digest for {child_name} · {school_name}
            </p>
        </div>
        <!-- Week label -->
        <div style="background: #f0f4ff; padding: 10px 32px; border-left: 4px solid #667eea;">
            <p style="margin: 0; color: #4a5568; font-size: 13px; font-weight: 600;">{week_label}</p>
        </div>
        <!-- Body -->
        <div style="background: white; padding: 24px 32px; border-radius: 0 0 12px 12px; border: 1px solid #e2e8f0; border-top: none;">
            {body_html}
            <hr style="margin: 24px 0; border: none; border-top: 1px solid #eee;">
            <p style="font-size: 12px; color: #a0aec0; text-align: center;">
                School Copilot automatically reads {child_name}'s school emails so you don't have to.<br>
                <a href="#" style="color: #667eea;">Open App</a> · <a href="#" style="color: #667eea;">Manage notifications</a>
            </p>
        </div>
    </div>
    """


def send_weekly_digest() -> bool:
    """
    Generate and send the weekly digest.
    Called by the scheduler every Sunday morning.
    Returns True if sent successfully.
    """
    child_name = config.CHILD_NAME or "your child"
    school_name = config.SCHOOL_NAME or "school"

    logger.info(f"Generating weekly digest for {child_name} at {school_name}")

    digest_text = _generate_digest_content(child_name, school_name)
    if not digest_text:
        logger.warning("Could not generate digest content — skipping")
        return False

    now = datetime.now()
    week_start = (now - timedelta(days=now.weekday())).strftime("%B %d")
    week_end = (now - timedelta(days=now.weekday()) + timedelta(days=6)).strftime("%B %d, %Y")
    week_label = f"Week of {week_start} – {week_end}"

    html = _render_digest_html(digest_text, child_name, school_name, week_label)
    subject = f"📘 {child_name}'s school this week — {week_label}"

    from app.notification_sender import send_weekly_digest as _send
    success = _send(html, subject)

    if success:
        logger.info("Weekly digest sent successfully")
    return success
