"""Notification service for new email detection and manual refresh."""
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

from app.config import config
from app.gmail_client import GmailClient, fetch_school_emails


NOTIFICATION_FILE = "data/.last_check.json"


def get_last_check_time() -> Optional[datetime]:
    """Get the timestamp of the last email check."""
    if not os.path.exists(NOTIFICATION_FILE):
        return None
    
    try:
        with open(NOTIFICATION_FILE, 'r') as f:
            data = json.load(f)
            timestamp_str = data.get('last_check')
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
    except (json.JSONDecodeError, IOError, ValueError):
        pass
    
    return None


def save_check_time(timestamp: Optional[datetime] = None) -> None:
    """Save the current check time."""
    if timestamp is None:
        timestamp = datetime.now()
    
    os.makedirs(os.path.dirname(NOTIFICATION_FILE), exist_ok=True)
    
    data = {
        'last_check': timestamp.isoformat(),
        'check_count': get_check_count() + 1
    }
    
    with open(NOTIFICATION_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_check_count() -> int:
    """Get the number of checks performed."""
    if not os.path.exists(NOTIFICATION_FILE):
        return 0
    
    try:
        with open(NOTIFICATION_FILE, 'r') as f:
            data = json.load(f)
            return data.get('check_count', 0)
    except (json.JSONDecodeError, IOError):
        return 0


def check_for_new_emails(manual: bool = False) -> Dict[str, Any]:
    """
    Check for new emails since last check.
    
    Args:
        manual: If True, this is a manual refresh (always checks)
        
    Returns:
        Dictionary with check results:
        {
            'has_new': bool,
            'new_count': int,
            'new_emails': list of email details,
            'from_lobeda': bool,
            'lobeda_emails': list,
            'last_check': datetime,
            'message': str
        }
    """
    last_check = get_last_check_time()
    
    # For manual refresh, always check
    if manual:
        last_check = None
    
    # Fetch recent emails (only need to check a few)
    try:
        emails = fetch_school_emails(max_results=20)  # Check more to catch all new ones
        
        if not emails:
            save_check_time()
            return {
                'has_new': False,
                'new_count': 0,
                'new_emails': [],
                'from_lobeda': False,
                'lobeda_emails': [],
                'last_check': datetime.now(),
                'message': 'No new emails found.'
            }
        
        # If we have a last check time, filter emails newer than that
        new_emails = []
        lobeda_emails = []
        
        if last_check:
            for email in emails:
                if email.date > last_check:
                    new_emails.append({
                        'subject': email.subject,
                        'sender': email.sender,
                        'date': email.date.isoformat(),
                        'id': email.id
                    })
                    # Check if from Miss Lobeda
                    if 'lobeda' in email.sender.lower() or 'grace.lobeda' in email.sender.lower():
                        lobeda_emails.append({
                            'subject': email.subject,
                            'sender': email.sender,
                            'date': email.date.isoformat(),
                            'id': email.id
                        })
        else:
            # First check or manual refresh - count all recent emails
            for email in emails[:10]:  # Check most recent 10
                new_emails.append({
                    'subject': email.subject,
                    'sender': email.sender,
                    'date': email.date.isoformat(),
                    'id': email.id
                })
                # Check if from Miss Lobeda
                if 'lobeda' in email.sender.lower() or 'grace.lobeda' in email.sender.lower():
                    lobeda_emails.append({
                        'subject': email.subject,
                        'sender': email.sender,
                        'date': email.date.isoformat(),
                        'id': email.id
                    })
        
        has_new = len(new_emails) > 0
        has_lobeda = len(lobeda_emails) > 0
        save_check_time()
        
        if has_new:
            message = f'Found {len(new_emails)} new email(s) since last check.'
            if has_lobeda:
                message += f' 🎯 {len(lobeda_emails)} from Miss Lobeda!'
            
            return {
                'has_new': True,
                'new_count': len(new_emails),
                'new_emails': new_emails,
                'from_lobeda': has_lobeda,
                'lobeda_emails': lobeda_emails,
                'last_check': datetime.now(),
                'message': message
            }
        else:
            return {
                'has_new': False,
                'new_count': 0,
                'new_emails': [],
                'from_lobeda': False,
                'lobeda_emails': [],
                'last_check': datetime.now(),
                'message': 'No new emails since last check.'
            }
    
    except Exception as e:
        return {
            'has_new': False,
            'new_count': 0,
            'new_emails': [],
            'from_lobeda': False,
            'lobeda_emails': [],
            'last_check': last_check,
            'message': f'Error checking for emails: {str(e)}',
            'error': True
        }


def get_notification_status() -> Dict[str, Any]:
    """Get current notification status."""
    last_check = get_last_check_time()
    
    return {
        'last_check': last_check.isoformat() if last_check else None,
        'check_count': get_check_count(),
        'auto_schedule_time': config.EMAIL_INGESTION_TIME,
        'next_auto_check': f"Today at {config.EMAIL_INGESTION_TIME}"
    }

