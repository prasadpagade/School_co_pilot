"""Track uploaded files to prevent duplicates."""
import os
import json
import hashlib
from pathlib import Path
from typing import Set


TRACKER_FILE = "data/.upload_tracker.json"
EMAIL_TRACKER_FILE = "data/.email_tracker.json"


def get_file_hash(filepath: str) -> str:
    """Get SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_tracker(filepath: str) -> Set[str]:
    """Load set of tracked items from JSON file."""
    if not os.path.exists(filepath):
        return set()
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return set(data.get('items', []))
    except (json.JSONDecodeError, IOError):
        return set()


def save_tracker(filepath: str, items: Set[str]) -> None:
    """Save set of tracked items to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    data = {
        'items': list(items),
        'count': len(items)
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def is_file_uploaded(filepath: str) -> bool:
    """Check if a file has already been uploaded."""
    tracker = load_tracker(TRACKER_FILE)
    
    # Use file path + modification time as identifier
    if os.path.exists(filepath):
        mtime = os.path.getmtime(filepath)
        file_id = f"{filepath}:{mtime}"
        return file_id in tracker
    
    return False


def mark_file_uploaded(filepath: str) -> None:
    """Mark a file as uploaded."""
    tracker = load_tracker(TRACKER_FILE)
    
    if os.path.exists(filepath):
        mtime = os.path.getmtime(filepath)
        file_id = f"{filepath}:{mtime}"
        tracker.add(file_id)
        save_tracker(TRACKER_FILE, tracker)


def clear_upload_tracker():
    """Clear upload tracker to force re-upload (useful for debugging)."""
    if os.path.exists(TRACKER_FILE):
        os.remove(TRACKER_FILE)
        print("Cleared upload tracker")


def is_email_processed(email_id: str) -> bool:
    """Check if an email has already been processed."""
    tracker = load_tracker(EMAIL_TRACKER_FILE)
    return email_id in tracker


def mark_email_processed(email_id: str) -> None:
    """Mark an email as processed."""
    tracker = load_tracker(EMAIL_TRACKER_FILE)
    tracker.add(email_id)
    save_tracker(EMAIL_TRACKER_FILE, tracker)


def get_tracker_stats() -> dict:
    """Get statistics about tracked items."""
    file_tracker = load_tracker(TRACKER_FILE)
    email_tracker = load_tracker(EMAIL_TRACKER_FILE)
    
    return {
        'uploaded_files': len(file_tracker),
        'processed_emails': len(email_tracker)
    }

