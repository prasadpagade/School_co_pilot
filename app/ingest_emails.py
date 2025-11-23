"""Script to ingest emails from Gmail and consolidate into master markdown."""
import os
import re
from pathlib import Path
from datetime import datetime

from app.gmail_client import fetch_school_emails
from app.config import config
from app.upload_tracker import is_email_processed, mark_email_processed
from app.markdown_consolidator import consolidate_email_with_attachments


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be filesystem-safe."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def save_email(email, output_dir: str) -> str:
    """
    Save email body to a text file.
    
    Args:
        email: Email object
        output_dir: Directory to save the email
        
    Returns:
        Path to saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Format filename: YYYY-MM-DD_subject.txt
    date_str = email.date.strftime("%Y-%m-%d")
    subject_safe = sanitize_filename(email.subject)
    filename = f"{date_str}_{subject_safe}.txt"
    
    # Ensure unique filename if it already exists
    filepath = os.path.join(output_dir, filename)
    counter = 1
    while os.path.exists(filepath):
        name, ext = os.path.splitext(filename)
        filepath = os.path.join(output_dir, f"{name}_{counter}{ext}")
        counter += 1
    
    # Write email content
    content = f"From: {email.sender}\n"
    content += f"Date: {email.date.isoformat()}\n"
    content += f"Subject: {email.subject}\n"
    content += f"Email ID: {email.id}\n"
    content += "\n" + "="*80 + "\n\n"
    content += email.body_text
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def save_attachment(attachment, email_id: str, output_dir: str) -> str:
    """
    Save email attachment to disk.
    
    Args:
        attachment: EmailAttachment object
        email_id: Email ID for organizing attachments
        output_dir: Directory to save attachments
        
    Returns:
        Path to saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Sanitize filename
    filename = sanitize_filename(attachment.filename)
    
    # If no filename, generate one based on mime type
    if not filename:
        ext = {
            'application/pdf': '.pdf',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'text/plain': '.txt',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        }.get(attachment.mime_type, '.bin')
        filename = f"attachment_{email_id[:8]}{ext}"
    
    # Ensure unique filename
    filepath = os.path.join(output_dir, filename)
    counter = 1
    while os.path.exists(filepath):
        name, ext = os.path.splitext(filename)
        filepath = os.path.join(output_dir, f"{name}_{counter}{ext}")
        counter += 1
    
    # Write attachment data
    with open(filepath, 'wb') as f:
        f.write(attachment.data)
    
    return filepath


def main():
    """Main ingestion function - consolidates emails into master markdown."""
    print("Starting email ingestion...")
    print(f"Looking for emails from: {config.SCHOOL_DOMAINS} or {config.SCHOOL_SENDERS}")
    
    # Fetch emails
    emails = fetch_school_emails(max_results=50)
    print(f"Found {len(emails)} school-related emails")
    
    if not emails:
        print("No emails found. Check your filters in .env")
        return
    
    # Process emails and consolidate (only new ones)
    processed_emails = 0
    processed_attachments = 0
    skipped_emails = 0
    temp_attachment_paths = []
    
    try:
        for email in emails:
            # Skip if already processed
            if is_email_processed(email.id):
                skipped_emails += 1
                continue
            
            print(f"\n📧 Processing email: {email.subject}")
            
            # Save attachments temporarily (needed for transcription)
            attachment_paths = []
            for attachment in email.attachments:
                attachment_path = save_attachment(
                    attachment, email.id, config.ATTACHMENTS_DIR
                )
                attachment_paths.append(attachment_path)
                temp_attachment_paths.append(attachment_path)
                processed_attachments += 1
                print(f"  📎 Saved attachment: {os.path.basename(attachment_path)}")
            
            # Consolidate email and attachments into markdown
            try:
                master_path = consolidate_email_with_attachments(
                    email_date=email.date,
                    email_subject=email.subject,
                    email_sender=email.sender,
                    email_body=email.body_text,
                    email_id=email.id,
                    attachment_paths=attachment_paths
                )
                processed_emails += 1
                mark_email_processed(email.id)
                print(f"  ✓ Consolidated email into: {master_path.name}")
            except Exception as e:
                print(f"  ✗ Error consolidating email: {e}")
                # Still mark as processed to avoid retrying
                mark_email_processed(email.id)
    
    finally:
        # Clean up temporary attachment files after consolidation
        print(f"\n🧹 Cleaning up temporary files...")
        cleaned = 0
        for att_path in temp_attachment_paths:
            try:
                if os.path.exists(att_path):
                    os.remove(att_path)
                    cleaned += 1
            except Exception as e:
                print(f"  ⚠️  Could not delete {os.path.basename(att_path)}: {e}")
        
        print(f"  ✓ Deleted {cleaned} temporary attachment files")
    
    print(f"\n✅ Ingestion complete!")
    print(f"  - Consolidated {processed_emails} new emails into master markdown")
    print(f"  - Processed {processed_attachments} attachments (transcribed and cleaned up)")
    if skipped_emails > 0:
        print(f"  - Skipped {skipped_emails} already processed emails")


if __name__ == "__main__":
    main()

