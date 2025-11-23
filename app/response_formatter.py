"""Format and enhance RAG responses to be action-oriented and well-structured."""
import re
from typing import List, Dict, Tuple
from datetime import datetime


def format_response_for_action(raw_response: str, question: str) -> str:
    """
    Format a raw RAG response to be action-oriented, well-structured, and easy to read.
    
    Args:
        raw_response: The raw response from RAG
        question: The original question
        
    Returns:
        Formatted, action-oriented response
    """
    if not raw_response or raw_response.strip() == "":
        return "I couldn't find information to answer your question. Please try rephrasing it."
    
    # Clean up the response
    formatted = raw_response.strip()
    
    # Detect response type and format accordingly
    question_lower = question.lower()
    
    # Format based on question type
    if any(word in question_lower for word in ["announcement", "news", "latest", "recent", "update"]):
        formatted = format_announcements(formatted)
    elif any(word in question_lower for word in ["when", "date", "time", "schedule", "next"]):
        formatted = format_dates_events(formatted)
    elif any(word in question_lower for word in ["policy", "rule", "guideline", "can", "should", "allow"]):
        formatted = format_policy(formatted)
    elif any(word in question_lower for word in ["what", "list", "tell me about"]):
        formatted = format_informational(formatted)
    else:
        formatted = format_general(formatted)
    
    # Add action items if dates/events are present
    formatted = add_action_items(formatted)
    
    # Improve markdown formatting
    formatted = improve_markdown_formatting(formatted)
    
    # Add visual separators for better readability
    formatted = add_visual_structure(formatted)
    
    return formatted


def format_announcements(text: str) -> str:
    """Format announcement-style responses."""
    # Ensure proper list formatting
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                formatted_lines.append('')
                in_list = False
            continue
        
        # Detect list items
        if re.match(r'^[\d\.\)\-\*]\s+', line) or line.startswith('•') or line.startswith('-'):
            if not in_list:
                formatted_lines.append('')
            formatted_lines.append(f"**{line.lstrip('0123456789.)•-* ')}**")
            in_list = True
        else:
            if in_list:
                formatted_lines.append('')
                in_list = False
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)


def format_dates_events(text: str) -> str:
    """Format date/event responses with clear action items."""
    # Extract dates and make them prominent
    date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b'
    
    def highlight_date(match):
        date_str = match.group(1)
        return f"**📅 {date_str}**"
    
    text = re.sub(date_pattern, highlight_date, text, flags=re.IGNORECASE)
    
    # Add action-oriented headers
    if "next" in text.lower() or "upcoming" in text.lower():
        text = "**🎯 Upcoming Events:**\n\n" + text
    
    return text


def format_policy(text: str) -> str:
    """Format policy responses with clear action items."""
    # Structure policy information
    lines = text.split('\n')
    formatted = []
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect section headers
        if ':' in line and len(line) < 100:
            if current_section:
                formatted.append('')
            formatted.append(f"**{line}**")
            current_section = line
        else:
            # Format requirements/restrictions
            if any(word in line.lower() for word in ['must', 'should', 'required', 'need', 'cannot', 'not allowed']):
                formatted.append(f"  ⚠️ {line}")
            elif any(word in line.lower() for word in ['can', 'may', 'allowed', 'optional']):
                formatted.append(f"  ✅ {line}")
            else:
                formatted.append(f"  • {line}")
    
    return '\n'.join(formatted)


def format_informational(text: str) -> str:
    """Format informational responses."""
    # Break into clear sections
    lines = text.split('\n')
    formatted = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted.append('')
            continue
        
        # Make headers bold
        if line.endswith(':') and len(line) < 80:
            formatted.append(f"**{line}**")
        elif re.match(r'^[\d\.]+\s+', line):  # Numbered list
            formatted.append(f"**{line}**")
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)


def format_general(text: str) -> str:
    """Format general responses."""
    # Ensure proper paragraph breaks
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
    return text


def add_action_items(text: str) -> str:
    """Add action items section if dates/events are present."""
    # Check if there are dates in the response
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',
        r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\w+\s+\d{1,2}\b'
    ]
    
    has_dates = any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)
    
    if has_dates and "📅" not in text:
        # Add a note about calendar integration
        text += "\n\n---\n\n💡 **Tip:** I can add these events to your calendar! Just ask me to add them."
    
    return text


def improve_markdown_formatting(text: str) -> str:
    """Improve markdown formatting for better readability."""
    # Ensure proper list formatting
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    list_type = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect list items
        if re.match(r'^[\*\-\•]\s+', stripped):
            if not in_list:
                formatted_lines.append('')
            formatted_lines.append(stripped)
            in_list = True
            list_type = 'ul'
        elif re.match(r'^\d+[\.\)]\s+', stripped):
            if not in_list or list_type != 'ol':
                if in_list:
                    formatted_lines.append('')
                formatted_lines.append('')
            formatted_lines.append(stripped)
            in_list = True
            list_type = 'ol'
        else:
            if in_list:
                formatted_lines.append('')
                in_list = False
                list_type = None
            if stripped:
                formatted_lines.append(stripped)
            elif i < len(lines) - 1:  # Don't add extra blank at end
                formatted_lines.append('')
    
    # Clean up excessive blank lines
    result = '\n'.join(formatted_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


def add_visual_structure(text: str) -> str:
    """Add visual structure with emojis and formatting."""
    lines = text.split('\n')
    formatted = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            formatted.append('')
            continue
        
        # Add emojis to common patterns
        if re.match(r'^[\*\-\•]\s+', stripped):
            # List item - ensure it has proper formatting
            content = re.sub(r'^[\*\-\•]\s+', '', stripped)
            if not content.startswith('📅') and not content.startswith('⚠️') and not content.startswith('✅'):
                # Check if it's a date/event
                if re.search(r'\b\d{1,2}[/-]\d{1,2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', content, re.IGNORECASE):
                    formatted.append(f"• 📅 {content}")
                else:
                    formatted.append(f"• {content}")
            else:
                formatted.append(f"• {content}")
        elif stripped.endswith(':') and len(stripped) < 80:
            # Section header
            if not stripped.startswith('**'):
                formatted.append(f"**{stripped}**")
            else:
                formatted.append(stripped)
        else:
            formatted.append(stripped)
    
    return '\n'.join(formatted)


def extract_action_items(text: str) -> List[str]:
    """Extract actionable items from text."""
    action_items = []
    
    # Look for dates with actions
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})'
    dates = re.findall(date_pattern, text, re.IGNORECASE)
    
    for date in dates:
        # Find context around the date
        date_index = text.find(date)
        if date_index != -1:
            context_start = max(0, date_index - 50)
            context_end = min(len(text), date_index + len(date) + 50)
            context = text[context_start:context_end]
            action_items.append(f"📅 {date}: {context.strip()}")
    
    return action_items

