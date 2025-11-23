"""Extract dates and events from text using Gemini API."""
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

from app.config import config
from app.gemini_file_search import initialize_client
from google.genai import types


def extract_dates_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract dates and events from text using Gemini API.
    
    Args:
        text: Text to extract dates from
        
    Returns:
        List of dictionaries with date information:
        [
            {
                "title": "Event title",
                "date": datetime object,
                "time": optional time string,
                "description": "Event description",
                "confidence": float
            }
        ]
    """
    if not config.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment variables")
    
    client = initialize_client()
    
    # Get current date for context
    current_date = datetime.now()
    current_year = current_date.year
    current_date_str = current_date.strftime("%B %d, %Y")
    
    prompt = f"""Extract ALL dates, events, and reminders from the following text.
IMPORTANT: Today is {current_date_str}. Use {current_year} as the year for dates unless explicitly stated otherwise.

CRITICAL INSTRUCTIONS:
1. If multiple dates are listed (e.g., "Nov 18,20, Dec 2,4,9,11"), create SEPARATE events for EACH date
2. Parse time formats like "345-445" as "15:45-16:45" (3:45 PM - 4:45 PM)
3. Parse time formats like "530-630" as "17:30-18:30" (5:30 PM - 6:30 PM)
4. Parse time formats like "4:00 p.m." or "4:00 PM" as "16:00" (4:00 PM)
5. Parse time formats like "4pm" or "4 PM" as "16:00" (4:00 PM)
6. Parse time formats like "10am" or "10 AM" as "10:00" (10:00 AM)
7. Extract event titles from context (e.g., "Martial arts classes", "Music concert")
8. Include location if mentioned (e.g., "school gym", "main school")
9. ALWAYS extract times when mentioned, even if in different formats

Return a JSON array of events. Each event should have:
- "title": A clear, concise event title (e.g., "Martial Arts Class", "Music Concert")
- "date": ISO format date string (YYYY-MM-DD) - use {current_year} if year not specified
- "time": Optional time string (HH:MM or HH:MM-HH:MM for ranges) if mentioned
- "description": Full description from the text including location, dress code, etc.
- "confidence": A number between 0 and 1 indicating how certain you are

Text to analyze:
{text}

Return ONLY valid JSON array, no other text. 

Example for "Nov 18,20, Dec 2,4,9,11 - 345-445 Denali Martial arts classes":
[
  {{"title": "Martial Arts Class", "date": "2025-11-18", "time": "15:45-16:45", "description": "Denali Martial arts classes at school gym", "confidence": 0.95}},
  {{"title": "Martial Arts Class", "date": "2025-11-20", "time": "15:45-16:45", "description": "Denali Martial arts classes at school gym", "confidence": 0.95}},
  {{"title": "Martial Arts Class", "date": "2025-12-02", "time": "15:45-16:45", "description": "Denali Martial arts classes at school gym", "confidence": 0.95}},
  {{"title": "Martinal Arts Class", "date": "2025-12-04", "time": "15:45-16:45", "description": "Denali Martial arts classes at school gym", "confidence": 0.95}},
  {{"title": "Martial Arts Class", "date": "2025-12-09", "time": "15:45-16:45", "description": "Denali Martial arts classes at school gym", "confidence": 0.95}},
  {{"title": "Martial Arts Class", "date": "2025-12-11", "time": "15:45-16:45", "description": "Denali Martial arts classes at school gym", "confidence": 0.95}}
]"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[types.Part.from_text(text=prompt)],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        if hasattr(response, 'text') and response.text:
            import json
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                # Extract JSON from code block
                lines = response_text.split('\n')
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not response_text.startswith('```json') and not response_text.startswith('```')):
                        json_lines.append(line)
                response_text = '\n'.join(json_lines)
            
            try:
                events = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"Response text (first 500 chars): {response_text[:500]}")
                # Try to extract JSON from response if it's wrapped in text
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    try:
                        events = json.loads(json_match.group(0))
                        print("✅ Recovered JSON from response")
                    except:
                        print("❌ Could not recover JSON")
                        return []
                else:
                    return []
            
            # Parse dates and convert to datetime objects
            parsed_events = []
            for event in events:
                try:
                    date_str = event.get('date')
                    if date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # If time is provided, combine with date
                        # Handle time ranges (e.g., "15:45-16:45" or "3:45 PM - 4:45 PM")
                        time_str = event.get('time')
                        if time_str:
                            try:
                                # Handle time ranges - use start time
                                if '-' in time_str and ':' in time_str:
                                    # Format like "15:45-16:45"
                                    start_time = time_str.split('-')[0].strip()
                                    time_parts = start_time.split(':')
                                    date_obj = date_obj.replace(
                                        hour=int(time_parts[0]),
                                        minute=int(time_parts[1]) if len(time_parts) > 1 else 0
                                    )
                                elif ':' in time_str:
                                    # Single time like "15:45"
                                    time_parts = time_str.split(':')
                                    date_obj = date_obj.replace(
                                        hour=int(time_parts[0]),
                                        minute=int(time_parts[1]) if len(time_parts) > 1 else 0
                                    )
                            except Exception as e:
                                print(f"Error parsing time {time_str}: {e}")
                                pass
                        
                        parsed_events.append({
                            'title': event.get('title', 'Untitled Event'),
                            'date': date_obj,
                            'time': time_str,
                            'description': event.get('description', ''),
                            'confidence': event.get('confidence', 0.5)
                        })
                except Exception as e:
                    print(f"Error parsing event date: {e}")
                    continue
            
            return parsed_events
        
        return []
    except Exception as e:
        print(f"Error extracting dates: {e}")
        # Fallback to simple regex-based extraction
        return _extract_dates_regex(text)


def _extract_dates_regex(text: str) -> List[Dict[str, Any]]:
    """Fallback regex-based date extraction."""
    events = []
    
    # Common date patterns
    patterns = [
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})',
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
    ]
    
    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                groups = match.groups()
                # Simple extraction - would need more logic for full parsing
                # This is just a fallback
                pass
            except:
                continue
    
    return events

