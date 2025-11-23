"""Configuration management for Denali School Copilot."""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        self.FILE_SEARCH_STORE_NAME = os.getenv("FILE_SEARCH_STORE_NAME", "")
        self.SCHOOL_DOMAINS = self._parse_list(os.getenv("SCHOOL_DOMAINS", ""))
        self.SCHOOL_SENDERS = self._parse_list(os.getenv("SCHOOL_SENDERS", ""))
        self.GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
        self.GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
        self.GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost")
        
        # Gmail API scopes
        self.GMAIL_SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
        
        # File paths
        self.CREDENTIALS_FILE = "credentials.json"
        self.TOKEN_FILE = "token.json"
        self.RAW_EMAILS_DIR = "data/raw_emails"
        self.ATTACHMENTS_DIR = "data/attachments"
        self.CONSOLIDATED_DIR = "data/consolidated"
        
        # Calendar settings
        self.CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
        self.DEFAULT_CALENDAR_ATTENDEES = self._parse_list(os.getenv("DEFAULT_CALENDAR_ATTENDEES", ""))
        self.EMAIL_INGESTION_TIME = os.getenv("EMAIL_INGESTION_TIME", "18:00")  # 6pm default
    
    @staticmethod
    def _parse_list(value: str) -> List[str]:
        """Parse comma-separated string into list, stripping whitespace."""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]


# Global config instance
config = Config()

