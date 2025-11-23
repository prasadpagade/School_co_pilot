"""Consolidate emails and attachments into a master markdown file."""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import config
from app.attachment_transcriber import transcribe_attachment


# Maximum file size before splitting (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes


def get_master_markdown_path() -> Path:
    """
    Get the path to the master markdown file.
    Creates a weekly file: school-data-YYYY-WWW.md
    
    Returns:
        Path to the master markdown file
    """
    # Create consolidated data directory
    consolidated_dir = Path("data/consolidated")
    consolidated_dir.mkdir(parents=True, exist_ok=True)
    
    # Use weekly file naming: school-data-YYYY-WWW.md
    current_date = datetime.now()
    year_week = current_date.strftime("%Y-W%V")  # e.g., "2025-W47"
    filename = f"school-data-{year_week}.md"
    
    return consolidated_dir / filename


def should_create_new_file(file_path: Path) -> bool:
    """
    Decide if a new file should be created.
    
    Criteria:
    1. If file doesn't exist, create it
    2. If file size > MAX_FILE_SIZE, create new one
    3. Otherwise, append to existing
    
    Args:
        file_path: Path to the current markdown file
        
    Returns:
        True if new file should be created, False to append
    """
    if not file_path.exists():
        return True
    
    # Check if file size exceeds limit
    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        print(f"  ⚠️  File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit, creating new file")
        return True
    
    return False


def create_markdown_header() -> str:
    """
    Create the header for the markdown file.
    
    Returns:
        Markdown header string
    """
    current_date = datetime.now()
    date_str = current_date.strftime("%Y-%m-%d %H:%M:%S")
    year_week = current_date.strftime("%Y-W%V")
    
    return f"""# School Emails & Announcements

**Generated:** {date_str}  
**Week:** {year_week}  
**Source:** Gmail School Inbox

---

"""


def format_email_markdown(
    email_date: datetime,
    email_subject: str,
    email_sender: str,
    email_body: str,
    email_id: str,
    attachments: List[Tuple[str, str]] = None
) -> str:
    """
    Format a single email as markdown section.
    
    Args:
        email_date: Date of the email
        email_subject: Subject line
        email_sender: Sender email address
        email_body: Email body text
        email_id: Gmail message ID
        attachments: List of (attachment_path, transcribed_text) tuples
        
    Returns:
        Formatted markdown string
    """
    date_str = email_date.strftime("%Y-%m-%d")
    time_str = email_date.strftime("%H:%M:%S")
    
    markdown = f"""## Email: {date_str} - {email_subject}

**From:** {email_sender}  
**Date:** {date_str} {time_str}  
**Email ID:** {email_id}

{email_body}
"""
    
    # Add attachments if any
    if attachments and len(attachments) > 0:
        markdown += "\n### Attachments:\n\n"
        for att_path, transcribed_text in attachments:
            filename = os.path.basename(att_path)
            markdown += f"#### {filename}\n\n"
            markdown += f"{transcribed_text}\n\n"
    
    markdown += "\n---\n\n"
    
    return markdown


def append_to_master_markdown(email_content: str, file_path: Path) -> Path:
    """
    Append email content to master markdown file.
    Creates new file if needed (weekly or if file too large).
    
    Args:
        email_content: Markdown-formatted email content
        file_path: Path to the master markdown file
        
    Returns:
        Path to the file that was written to
    """
    # Check if we need to create a new file
    if should_create_new_file(file_path):
        # If file exists but is too large, create a new one with suffix
        if file_path.exists():
            counter = 1
            base_path = file_path
            while file_path.exists():
                stem = base_path.stem
                file_path = base_path.parent / f"{stem}_part{counter}.md"
                counter += 1
        
        # Create new file with header
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(create_markdown_header())
            f.write(email_content)
        print(f"  ✓ Created new markdown file: {file_path.name}")
    else:
        # Append to existing file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(email_content)
        print(f"  ✓ Appended to markdown file: {file_path.name}")
    
    return file_path


def consolidate_email_with_attachments(
    email_date: datetime,
    email_subject: str,
    email_sender: str,
    email_body: str,
    email_id: str,
    attachment_paths: List[str] = None
) -> Path:
    """
    Consolidate a single email and its attachments into the master markdown file.
    
    Args:
        email_date: Date of the email
        email_subject: Subject line
        email_sender: Sender email address
        email_body: Email body text
        email_id: Gmail message ID
        attachment_paths: List of paths to attachment files
        
    Returns:
        Path to the markdown file that was updated
    """
    # Get master markdown file path
    master_path = get_master_markdown_path()
    
    # Transcribe attachments
    transcribed_attachments = []
    if attachment_paths:
        for att_path in attachment_paths:
            try:
                if os.path.exists(att_path):
                    transcribed_text = transcribe_attachment(att_path)
                    transcribed_attachments.append((att_path, transcribed_text))
                else:
                    print(f"  ⚠️  Attachment not found: {att_path}")
            except Exception as e:
                print(f"  ✗ Error transcribing {os.path.basename(att_path)}: {e}")
                transcribed_attachments.append((att_path, f"[Error transcribing attachment: {str(e)}]"))
    
    # Format email as markdown
    email_markdown = format_email_markdown(
        email_date=email_date,
        email_subject=email_subject,
        email_sender=email_sender,
        email_body=email_body,
        email_id=email_id,
        attachments=transcribed_attachments
    )
    
    # Append to master file
    return append_to_master_markdown(email_markdown, master_path)


def get_latest_markdown_file() -> Optional[Path]:
    """
    Get the latest consolidated markdown file.
    
    Returns:
        Path to the latest markdown file, or None if none exists
    """
    consolidated_dir = Path("data/consolidated")
    
    if not consolidated_dir.exists():
        return None
    
    # Find all markdown files, sort by modification time
    md_files = sorted(
        consolidated_dir.glob("school-data-*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    return md_files[0] if md_files else None

