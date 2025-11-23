"""Google Calendar integration for creating events and sharing calendars."""
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import config


# Google Calendar API scopes
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]


class CalendarClient:
    """Client for interacting with Google Calendar API."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
    
    def authenticate(self) -> None:
        """Authenticate with Google Calendar API."""
        creds = None
        token_file = "calendar_token.json"
        
        if os.path.exists(token_file):
            try:
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"Warning: Could not load existing calendar token: {e}")
                os.remove(token_file)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Calendar token refresh failed: {e}")
                    creds = None
            
            if not creds or not creds.valid:
                if not os.path.exists(config.CREDENTIALS_FILE):
                    error_msg = (
                        f"Calendar credentials not found: {config.CREDENTIALS_FILE}\n\n"
                        "To set up Google Calendar integration:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Enable 'Google Calendar API'\n"
                        "3. Create OAuth credentials (Desktop app)\n"
                        "4. Download and save as 'credentials.json'\n"
                        "5. See CALENDAR_SETUP_GUIDE.md for detailed instructions"
                    )
                    raise FileNotFoundError(error_msg)
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.CREDENTIALS_FILE, CALENDAR_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    error_str = str(e)
                    if "access_denied" in error_str or "403" in error_str:
                        detailed_error = (
                            f"Calendar OAuth authentication failed: {e}\n\n"
                            "This usually means:\n"
                            "1. Google Calendar API is not enabled in Google Cloud Console\n"
                            "2. OAuth consent screen is not configured\n"
                            "3. Your email is not added as a test user\n\n"
                            "See CALENDAR_SETUP_GUIDE.md for detailed setup instructions."
                        )
                        raise Exception(detailed_error)
                    raise Exception(f"Calendar OAuth authentication failed: {e}")
            
            try:
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"Warning: Could not save calendar token: {e}")
        
        self.credentials = creds
        self.service = build('calendar', 'v3', credentials=creds)
    
    def create_event(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: Optional[datetime] = None,
        description: str = "",
        location: str = "",
        attendees: Optional[List[str]] = None,
        calendar_id: str = "primary",
        reminder_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Create a calendar event.
        
        Args:
            title: Event title
            start_datetime: Start date and time
            end_datetime: End date and time (defaults to 1 hour after start)
            description: Event description
            location: Event location
            attendees: List of email addresses to invite
            calendar_id: Calendar ID (default: "primary")
            reminder_minutes: Minutes before event for reminder (default: 60)
            
        Returns:
            Created event dictionary
        """
        if not self.service:
            self.authenticate()
        
        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=1)
        
        event = {
            'summary': title,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Denver',  # Adjust to your timezone
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Denver',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': reminder_minutes},
                    {'method': 'popup', 'minutes': reminder_minutes},
                ],
            },
        }
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        try:
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates='all' if attendees else 'none'
            ).execute()
            
            return created_event
        except HttpError as e:
            raise Exception(f"Error creating calendar event: {e}")
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars accessible to the user."""
        if not self.service:
            self.authenticate()
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get('items', [])
        except HttpError as e:
            raise Exception(f"Error listing calendars: {e}")
    
    def share_calendar(
        self,
        calendar_id: str,
        email: str,
        role: str = "reader"
    ) -> None:
        """
        Share a calendar with another user.
        
        Args:
            calendar_id: Calendar ID to share
            email: Email address to share with
            role: "reader", "writer", or "owner"
        """
        if not self.service:
            self.authenticate()
        
        try:
            rule = {
                'scope': {
                    'type': 'user',
                    'value': email,
                },
                'role': role,
            }
            
            self.service.acl().insert(
                calendarId=calendar_id,
                body=rule
            ).execute()
        except HttpError as e:
            raise Exception(f"Error sharing calendar: {e}")

