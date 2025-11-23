"""Gmail client for fetching school-related emails."""
import os
import base64
import pickle
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import config


@dataclass
class EmailAttachment:
    """Represents an email attachment."""
    filename: str
    mime_type: str
    data: bytes


@dataclass
class Email:
    """Represents a school email."""
    id: str
    subject: str
    sender: str
    date: datetime
    body_text: str
    attachments: List[EmailAttachment]


class GmailClient:
    """Client for interacting with Gmail API."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
    
    def authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(config.TOKEN_FILE):
            try:
                with open(config.TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"Warning: Could not load existing token: {e}")
                # Remove invalid token file
                os.remove(config.TOKEN_FILE)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    creds = None
            
            if not creds or not creds.valid:
                if not os.path.exists(config.CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Credentials file not found: {config.CREDENTIALS_FILE}. "
                        "Please download OAuth credentials from Google Cloud Console."
                    )
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.CREDENTIALS_FILE, config.GMAIL_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    error_msg = str(e)
                    if "access_denied" in error_msg or "403" in error_msg:
                        print("\n" + "="*80)
                        print("ERROR: OAuth Access Denied (403)")
                        print("="*80)
                        print("\nThis usually means:")
                        print("1. Gmail API is not enabled in Google Cloud Console")
                        print("2. OAuth consent screen is not configured")
                        print("3. Your email is not added as a test user")
                        print("\nPlease see TROUBLESHOOTING.md for detailed instructions.")
                        print("\nQuick fixes:")
                        print("- Enable Gmail API in Google Cloud Console")
                        print("- Configure OAuth consent screen (APIs & Services > OAuth consent screen)")
                        print("- Add your email as a test user")
                        print("="*80)
                    raise Exception(f"OAuth authentication failed: {e}")
            
            # Save credentials for next run
            try:
                with open(config.TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"Warning: Could not save token: {e}")
        
        self.credentials = creds
        self.service = build('gmail', 'v1', credentials=creds)
    
    def _build_query(self) -> str:
        """Build Gmail search query for school emails."""
        query_parts = []
        
        # Add domain filters
        if config.SCHOOL_DOMAINS:
            domain_queries = [f"from:{domain}" for domain in config.SCHOOL_DOMAINS]
            query_parts.append(f"({' OR '.join(domain_queries)})")
        
        # Add sender filters
        if config.SCHOOL_SENDERS:
            sender_queries = [f"from:{sender}" for sender in config.SCHOOL_SENDERS]
            query_parts.append(f"({' OR '.join(sender_queries)})")
        
        # Combine with OR if both exist
        if len(query_parts) > 1:
            base_query = f"({' OR '.join(query_parts)})"
        elif len(query_parts) == 1:
            base_query = query_parts[0]
        else:
            base_query = ""
        
        # Add date filter (last 30 days)
        if base_query:
            return f"{base_query} newer_than:30d"
        return "newer_than:30d"
    
    def _extract_email_body(self, message) -> str:
        """Extract plain text body from email message."""
        body = ""
        
        def _extract_from_payload(payload):
            """Recursively extract text from message payload."""
            text = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    text += _extract_from_payload(part)
            else:
                if payload.get('mimeType') == 'text/plain':
                    data = payload.get('body', {}).get('data', '')
                    if data:
                        text += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif payload.get('mimeType') == 'text/html':
                    # Fallback to HTML if plain text not available
                    data = payload.get('body', {}).get('data', '')
                    if data and not text:
                        html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Simple HTML stripping (basic implementation)
                        import re
                        text = re.sub('<[^<]+?>', '', html)
            return text
        
        if 'payload' in message:
            body = _extract_from_payload(message['payload'])
        
        return body.strip()
    
    def _extract_attachments(self, message) -> List[EmailAttachment]:
        """Extract attachments from email message."""
        attachments = []
        
        def _extract_from_payload(payload, message_id):
            """Recursively extract attachments from message payload."""
            if 'parts' in payload:
                for part in payload['parts']:
                    _extract_from_payload(part, message_id)
            else:
                filename = payload.get('filename', '')
                if filename and 'body' in payload and 'attachmentId' in payload['body']:
                    attachment_id = payload['body']['attachmentId']
                    mime_type = payload.get('mimeType', 'application/octet-stream')
                    
                    try:
                        attachment = self.service.users().messages().attachments().get(
                            userId='me',
                            messageId=message_id,
                            id=attachment_id
                        ).execute()
                        
                        data = base64.urlsafe_b64decode(attachment['data'])
                        attachments.append(EmailAttachment(
                            filename=filename,
                            mime_type=mime_type,
                            data=data
                        ))
                    except HttpError as e:
                        print(f"Error downloading attachment {filename}: {e}")
        
        if 'payload' in message:
            _extract_from_payload(message['payload'], message['id'])
        
        return attachments
    
    def fetch_school_emails(self, max_results: int = 50) -> List[Email]:
        """
        Fetch school-related emails from Gmail.
        
        Args:
            max_results: Maximum number of emails to fetch
            
        Returns:
            List of Email objects
        """
        if not self.service:
            self.authenticate()
        
        query = self._build_query()
        
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                try:
                    # Get full message
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Extract headers
                    headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
                    subject = headers.get('Subject', '(No Subject)')
                    sender = headers.get('From', 'Unknown')
                    date_str = headers.get('Date', '')
                    
                    # Parse date
                    try:
                        date = parsedate_to_datetime(date_str) if date_str else datetime.now()
                    except (ValueError, TypeError):
                        date = datetime.now()
                    
                    # Extract body and attachments
                    body_text = self._extract_email_body(message)
                    attachments = self._extract_attachments(message)
                    
                    emails.append(Email(
                        id=message['id'],
                        subject=subject,
                        sender=sender,
                        date=date,
                        body_text=body_text,
                        attachments=attachments
                    ))
                    
                except HttpError as e:
                    print(f"Error fetching message {msg['id']}: {e}")
                    continue
            
            return emails
            
        except HttpError as e:
            print(f"Error searching messages: {e}")
            return []


# Convenience function
def fetch_school_emails(max_results: int = 50) -> List[Email]:
    """Fetch school emails using default Gmail client."""
    client = GmailClient()
    return client.fetch_school_emails(max_results=max_results)

