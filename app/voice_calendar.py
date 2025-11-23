"""Process voice/text input to create calendar events."""
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.date_extractor import extract_dates_from_text
from app.calendar_client import CalendarClient
from app.config import config


def detect_calendar_intent(text: str) -> bool:
    """
    Detect if the user wants to create a calendar event.
    
    Keywords: add, create, schedule, reminder, calendar, event, appointment
    """
    calendar_keywords = [
        'add to calendar', 'create event', 'schedule', 'reminder',
        'calendar', 'add calendar', 'set reminder', 'add event',
        'appointment', 'book', 'plan'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in calendar_keywords)


def parse_voice_calendar_command(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse voice command to extract calendar event details.
    
    Examples:
    - "Add Music class on December 15th at 3pm"
    - "Create reminder for field trip tomorrow"
    - "Schedule parent teacher conference next week"
    """
    # First try to extract dates using the date extractor
    try:
        events = extract_dates_from_text(text)
        if events and len(events) > 0:
            # Use the first extracted event
            event = events[0]
            return {
                'title': event.get('title', 'Event'),
                'date': event.get('date'),
                'time': event.get('time'),
                'description': event.get('description', text),
                'confidence': event.get('confidence', 0.5)
            }
    except Exception as e:
        print(f"Error extracting dates: {e}")
    
    # Fallback: Try to parse manually
    # Look for date patterns
    date_patterns = [
        r'(?:on|for)\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?)',
        r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+)',
        r'(\w+\s+\d{1,2})',
    ]
    
    # Look for time patterns
    time_pattern = r'at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)'
    
    # Extract title (everything before date/time keywords)
    title_match = re.search(r'^(?:add|create|schedule|reminder|set)\s+(.+?)(?:\s+(?:on|for|at)|$)', text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else text
    
    # This is a simple fallback - the date extractor should handle most cases
    return None


def create_calendar_from_voice(text: str) -> Dict[str, Any]:
    """
    Process voice/text input and create calendar event.
    
    Args:
        text: Voice or text input (e.g., "Add Music class on December 15th at 3pm")
        
    Returns:
        Dictionary with result:
        {
            'success': bool,
            'event_id': str,
            'event_link': str,
            'message': str,
            'parsed_details': dict (what was extracted),
            'error': str (if failed)
        }
    """
    try:
        # Extract event details
        print(f"🔍 Parsing calendar command: {text}")
        events = extract_dates_from_text(text)
        
        if not events or len(events) == 0:
            return {
                'success': False,
                'message': '❌ Could not extract date or event details from your request.\n\nPlease try a format like:\n- "Add Music class on November 18th at 4:00 PM"\n- "Create event: Field trip on December 15th at 10am"',
                'error': 'No dates extracted',
                'parsed_details': None
            }
        
        # Use the first (most confident) event
        event_data = events[0]
        
        # Show what was parsed
        parsed_info = {
            'title': event_data.get('title', 'Untitled'),
            'date': event_data.get('date'),
            'time': event_data.get('time'),
            'description': event_data.get('description', '')[:100]
        }
        print(f"✅ Parsed event details: {parsed_info}")
        
        if not event_data.get('date'):
            return {
                'success': False,
                'message': '❌ Could not find a date in your request. Please include a date like "November 18th" or "Dec 15".',
                'error': 'No date found',
                'parsed_details': parsed_info
            }
        
        # Create calendar event
        calendar_client = CalendarClient()
        calendar_client.authenticate()
        
        # Get attendees from config
        attendees = config.DEFAULT_CALENDAR_ATTENDEES if config.DEFAULT_CALENDAR_ATTENDEES else None
        
        calendar_event = calendar_client.create_event(
            title=event_data.get('title', 'Event'),
            start_datetime=event_data['date'],
            description=event_data.get('description', text),
            attendees=attendees,
            calendar_id=config.CALENDAR_ID,
            reminder_minutes=60
        )
        
        # Format date/time for display
        date_str = event_data['date'].strftime('%B %d, %Y')
        time_str = ''
        if event_data.get('time'):
            time_str = f" at {event_data['time']}"
        
        return {
            'success': True,
            'event_id': calendar_event.get('id'),
            'event_link': calendar_event.get('htmlLink'),
            'message': f"✅ Calendar event created successfully!\n\n📅 **{event_data.get('title')}**\n📆 {date_str}{time_str}",
            'title': event_data.get('title'),
            'date': event_data['date'].isoformat(),
            'parsed_details': parsed_info
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error creating calendar event: {error_msg}")
        return {
            'success': False,
            'message': f'❌ Error creating calendar event: {error_msg}',
            'error': error_msg,
            'parsed_details': None
        }

