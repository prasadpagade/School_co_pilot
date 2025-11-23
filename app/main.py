"""FastAPI application for Denali School Copilot."""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import tempfile
from datetime import datetime
import logging
from functools import lru_cache

from app.config import config
from app.rag_chat import ask_school_question
from app.calendar_client import CalendarClient
from app.date_extractor import extract_dates_from_text
from app.image_processor import extract_text_from_image
from app.scheduler import scheduler
from app.notification_service import check_for_new_emails, get_notification_status
from app.rag_cache import get_cache_stats
from app.voice_calendar import detect_calendar_intent, create_calendar_from_voice

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv("ENVIRONMENT", "development") == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Denali School Copilot API",
    description="API for querying school-related information using RAG",
    version="0.1.0"
)

# Add GZip compression for production
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS configuration - more secure for production
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get static directory path (project root/static)
# __file__ is app/main.py, so we go up one level to get project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(_project_root, "static")

# Request logging middleware for production
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests in production."""
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    
    if os.getenv("ENVIRONMENT") == "production":
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
    
    return response


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str


class CalendarEventRequest(BaseModel):
    """Request model for creating calendar events."""
    title: str
    date: str  # ISO format: YYYY-MM-DD
    time: Optional[str] = None  # HH:MM format
    description: Optional[str] = ""
    location: Optional[str] = ""
    attendees: Optional[List[str]] = None
    reminder_minutes: Optional[int] = 60


class CalendarEventResponse(BaseModel):
    """Response model for calendar event creation."""
    success: bool
    event_id: Optional[str] = None
    event_link: Optional[str] = None
    message: str


class DateExtractionRequest(BaseModel):
    """Request model for date extraction."""
    text: str


class DateExtractionResponse(BaseModel):
    """Response model for date extraction."""
    events: List[dict]
    message: str
    extracted_text: Optional[str] = None  # For debugging


@app.get("/")
async def root():
    """Root endpoint - serve the UI."""
    ui_path = os.path.join(static_dir, "index.html")
    if os.path.exists(ui_path):
        return FileResponse(ui_path, media_type="text/html")
    return {
        "message": "Denali School Copilot API",
        "version": "0.1.0",
        "endpoints": {
            "/chat": "POST - Ask questions about school information",
            "/ui": "GET - Web UI for testing"
        }
    }

@app.get("/ui")
async def ui():
    """Serve the web UI."""
    ui_path = os.path.join(static_dir, "index.html")
    if os.path.exists(ui_path):
        return FileResponse(ui_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="UI not found")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for asking questions about school information.
    
    Args:
        request: ChatRequest with question field
        
    Returns:
        ChatResponse with answer field
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if not config.FILE_SEARCH_STORE_NAME:
        raise HTTPException(
            status_code=500,
            detail="FILE_SEARCH_STORE_NAME not configured. Please run init_file_search_store.py first."
        )
    
    try:
        import time
        start_time = time.time()
        answer = ask_school_question(request.question, config.FILE_SEARCH_STORE_NAME)
        response_time = time.time() - start_time
        
        logger.info(f"Chat query processed in {response_time:.3f}s")
        
        # Tracking is now done inside ask_school_question with quality scoring
        # No need to track here to avoid double tracking
        
        return ChatResponse(answer=answer)
    except Exception as e:
        error_msg = str(e)
        # Don't expose internal errors to users, provide helpful message
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait a moment and try again."
            )
        raise HTTPException(status_code=500, detail=f"Error processing question: {error_msg}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "store_configured": bool(config.FILE_SEARCH_STORE_NAME),
        "next_email_ingestion": scheduler.get_next_run_time()
    }


@app.post("/upload-image", response_model=DateExtractionResponse)
async def upload_image(file: UploadFile = File(...), debug: bool = False):
    """
    Upload an image (conversation screenshot) and extract dates/events.
    
    Args:
        file: Image file to upload
        debug: If True, include extracted text in response
        
    Returns:
        Extracted dates and events
    """
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Extract text from image
        extracted_text = extract_text_from_image(tmp_path)
        
        # Extract dates from text
        events = extract_dates_from_text(extracted_text)
        
        response_data = {
            "events": events,
            "message": f"Extracted {len(events)} event(s) from image"
        }
        
        # Include extracted text in debug mode
        if debug:
            response_data["extracted_text"] = extracted_text[:500]  # First 500 chars
        
        return DateExtractionResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/extract-dates", response_model=DateExtractionResponse)
async def extract_dates(request: DateExtractionRequest):
    """
    Extract dates and events from text.
    
    Args:
        request: Text to extract dates from
        
    Returns:
        Extracted dates and events
    """
    try:
        events = extract_dates_from_text(request.text)
        
        return DateExtractionResponse(
            events=events,
            message=f"Extracted {len(events)} event(s) from text"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting dates: {str(e)}")


@app.get("/calendar/status")
async def get_calendar_status():
    """Check calendar integration status."""
    status = {
        "configured": False,
        "authenticated": False,
        "message": "",
        "setup_required": []
    }
    
    # Check if credentials file exists
    if not os.path.exists(config.CREDENTIALS_FILE):
        status["message"] = "Calendar credentials not found. Setup required."
        status["setup_required"] = [
            "Enable Google Calendar API in Google Cloud Console",
            "Create OAuth credentials",
            "Download credentials.json file"
        ]
        return status
    
    status["configured"] = True
    
    # Check if authenticated
    token_file = "calendar_token.json"
    if os.path.exists(token_file):
        try:
            import pickle
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
            if creds and creds.valid:
                status["authenticated"] = True
                status["message"] = "Calendar is connected and ready"
            else:
                status["message"] = "Calendar token expired. Re-authentication needed."
        except:
            status["message"] = "Calendar token invalid. Re-authentication needed."
    else:
        status["message"] = "Calendar not authenticated. First use will prompt for authorization."
    
    return status


@app.post("/create-calendar-event", response_model=CalendarEventResponse)
async def create_calendar_event(request: CalendarEventRequest):
    """
    Create a calendar event.
    
    Args:
        request: Calendar event details
        
    Returns:
        Created event information
    """
    try:
        # Check if credentials exist
        if not os.path.exists(config.CREDENTIALS_FILE):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Calendar not set up. Please:\n"
                    "1. Enable Google Calendar API in Google Cloud Console\n"
                    "2. Create OAuth credentials\n"
                    "3. Save as 'credentials.json'\n"
                    "See CALENDAR_SETUP_GUIDE.md for details"
                )
            )
        
        # Parse date and time
        date_obj = datetime.strptime(request.date, '%Y-%m-%d')
        
        if request.time:
            time_parts = request.time.split(':')
            date_obj = date_obj.replace(
                hour=int(time_parts[0]),
                minute=int(time_parts[1]) if len(time_parts) > 1 else 0
            )
        else:
            # Default to 9am if no time specified
            date_obj = date_obj.replace(hour=9, minute=0)
        
        # Use default attendees if none provided
        attendees = request.attendees or config.DEFAULT_CALENDAR_ATTENDEES
        
        # Create calendar client and event
        calendar_client = CalendarClient()
        calendar_client.authenticate()
        
        event = calendar_client.create_event(
            title=request.title,
            start_datetime=date_obj,
            description=request.description or "",
            location=request.location or "",
            attendees=attendees if attendees else None,
            calendar_id=config.CALENDAR_ID,
            reminder_minutes=request.reminder_minutes or 60
        )
        
        return CalendarEventResponse(
            success=True,
            event_id=event.get('id'),
            event_link=event.get('htmlLink'),
            message=f"Calendar event '{request.title}' created successfully"
        )
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        error_msg = str(e)
        # Provide helpful error messages
        if "Calendar API" in error_msg or "not enabled" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Google Calendar API not enabled.\n"
                    "Please enable it in Google Cloud Console:\n"
                    "https://console.cloud.google.com/apis/library/calendar-json.googleapis.com"
                )
            )
        raise HTTPException(status_code=500, detail=f"Error creating calendar event: {error_msg}")


@app.post("/process-conversation-image")
async def process_conversation_image(
    file: UploadFile = File(...),
    attendees: Optional[str] = Form(None)
):
    """
    Process a conversation image, extract dates, and optionally create calendar events.
    
    This is a convenience endpoint that combines image upload, date extraction,
    and calendar event creation in one call.
    
    Args:
        file: Image file (conversation screenshot)
        attendees: Comma-separated list of email addresses (optional)
        
    Returns:
        Extracted events and created calendar events
    """
    # First extract dates from image
    try:
        extraction_response = await upload_image(file, debug=False)
        events = extraction_response.events
        
        # Log for debugging
        if not events:
            print(f"⚠️  No events extracted from image. Extracted text length: {len(extraction_response.extracted_text) if extraction_response.extracted_text else 0}")
    except Exception as e:
        import traceback
        print(f"❌ Error in process_conversation_image: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error processing image: {str(e)}",
            "events": []
        }
    
    if not events:
        return {
            "success": False,
            "message": "No dates or events found in the image. The image may not contain clear date information, or the text extraction may have failed. Please try:\n1. Ensure the image is clear and readable\n2. Make sure dates are visible in the image\n3. Try a different image format",
            "events": []
        }
    
    # Parse attendees
    attendee_list = []
    if attendees:
        attendee_list = [email.strip() for email in attendees.split(',') if email.strip()]
    elif config.DEFAULT_CALENDAR_ATTENDEES:
        attendee_list = config.DEFAULT_CALENDAR_ATTENDEES
    
    # Create calendar events for each extracted event
    created_events = []
    calendar_client = CalendarClient()
    
    try:
        calendar_client.authenticate()
    except Exception as e:
        return {
            "success": False,
            "message": f"Calendar authentication failed: {str(e)}",
            "events": events,
            "created_events": []
        }
    
    for event in events:
        try:
            calendar_event = calendar_client.create_event(
                title=event['title'],
                start_datetime=event['date'],
                description=event.get('description', ''),
                attendees=attendee_list if attendee_list else None,
                calendar_id=config.CALENDAR_ID,
                reminder_minutes=60
            )
            created_events.append({
                "title": event['title'],
                "date": event['date'].isoformat(),
                "event_id": calendar_event.get('id'),
                "event_link": calendar_event.get('htmlLink')
            })
        except Exception as e:
            created_events.append({
                "title": event['title'],
                "error": str(e)
            })
    
    return {
        "success": True,
        "message": f"Created {len(created_events)} calendar event(s)",
        "events": events,
        "created_events": created_events
    }


@app.get("/schedule/status")
async def get_schedule_status():
    """Get the status of scheduled email ingestion."""
    return {
        "scheduled": scheduler.scheduler.get_job('daily_email_ingestion') is not None,
        "next_run": scheduler.get_next_run_time(),
        "ingestion_time": config.EMAIL_INGESTION_TIME
    }


@app.post("/check-new-emails")
async def check_new_emails_endpoint():
    """
    Manually check for new emails (cost-efficient - only checks recent emails).
    Returns notification status without ingesting.
    """
    result = check_for_new_emails(manual=True)
    return result


@app.get("/notification/status")
async def get_notification_status_endpoint():
    """Get notification status and last check time."""
    status = get_notification_status()
    return status


@app.get("/cache/stats")
async def get_cache_stats_endpoint():
    """Get RAG cache statistics."""
    return get_cache_stats()


@app.get("/rag/metrics")
async def get_rag_metrics():
    """Get RAG performance metrics and improvement suggestions."""
    from app.rag_improvement import get_metrics_summary
    return get_metrics_summary()


@app.post("/rag/feedback")
async def submit_feedback(question: str, answer: str, helpful: bool, comment: Optional[str] = None):
    """Submit feedback on a RAG response for self-improvement."""
    from app.rag_improvement import record_feedback
    record_feedback(question, answer, helpful, comment)
    return {"status": "feedback_recorded"}


class VoiceCalendarRequest(BaseModel):
    """Request model for voice calendar creation."""
    text: str


@app.post("/voice-calendar", response_model=CalendarEventResponse)
async def voice_calendar(request: VoiceCalendarRequest):
    """
    Create a calendar event from voice or text input.
    
    Examples:
    - "Add Music class on December 15th at 3pm"
    - "Create reminder for field trip tomorrow"
    - "Schedule parent teacher conference next week"
    
    Args:
        request: VoiceCalendarRequest with text field
        
    Returns:
        CalendarEventResponse with event details
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        result = create_calendar_from_voice(request.text)
        
        if result['success']:
            return CalendarEventResponse(
                success=True,
                event_id=result.get('event_id'),
                event_link=result.get('event_link'),
                message=result.get('message', 'Calendar event created successfully')
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get('message', 'Failed to create calendar event')
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice calendar request: {str(e)}")


# Initialize scheduler on startup
@app.get("/emails/recent")
async def get_recent_emails():
    """Get recent emails and announcements."""
    import glob
    from pathlib import Path
    
    emails_dir = Path(config.RAW_EMAILS_DIR)
    if not emails_dir.exists():
        return {
            "emails": [],
            "last_ingestion": None,
            "total_count": 0
        }
    
    # Get all email files, sorted by date in filename (newest first), then by modification time
    email_files = list(emails_dir.glob("*.txt"))
    
    # Sort by date in filename (YYYY-MM-DD), then by modification time
    def get_sort_key(filepath):
        filename = filepath.name
        # Extract date from filename (format: YYYY-MM-DD_subject.txt)
        if '_' in filename:
            date_str = filename.split('_')[0]
            try:
                # Parse date for proper sorting
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return (date_obj, filepath.stat().st_mtime)
            except:
                return (datetime.min, filepath.stat().st_mtime)
        return (datetime.min, filepath.stat().st_mtime)
    
    email_files = sorted(email_files, key=get_sort_key, reverse=True)
    
    recent_emails = []
    for email_file in email_files[:10]:  # Last 10 emails
        try:
            with open(email_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract subject from filename or content
                filename = email_file.name
                subject = filename.split('_', 1)[1].replace('.txt', '') if '_' in filename else filename
                
                # Extract date from filename
                date_str = filename.split('_')[0] if '_' in filename else None
                
                # Extract sender and date from content
                sender = 'Unknown'
                email_date = date_str
                for line in content.split('\n')[:10]:
                    if line.startswith('From:'):
                        sender = line.replace('From:', '').strip()
                    elif line.startswith('Date:'):
                        try:
                            from datetime import datetime
                            from email.utils import parsedate_to_datetime
                            date_line = line.replace('Date:', '').strip()
                            parsed_date = parsedate_to_datetime(date_line)
                            email_date = parsed_date.strftime('%Y-%m-%d') if parsed_date else date_str
                        except:
                            pass
                
                # Get first few lines for preview
                preview = content.split('\n')[:5]
                preview_text = '\n'.join(preview)
                
                recent_emails.append({
                    "subject": subject,
                    "date": email_date,
                    "sender": sender,
                    "preview": preview_text[:200],
                    "filename": filename
                })
        except Exception as e:
            continue
    
    # Get last check time
    from app.notification_service import get_last_check_time
    last_check = get_last_check_time()
    
    return {
        "emails": recent_emails,
        "last_ingestion": last_check.isoformat() if last_check else None,
        "total_count": len(email_files)
    }


@app.on_event("startup")
async def startup_event():
    """Initialize scheduled tasks on application startup."""
    # Parse ingestion time (format: HH:MM)
    try:
        time_parts = config.EMAIL_INGESTION_TIME.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        scheduler.schedule_daily_ingestion(hour=hour, minute=minute)
        print(f"✅ Scheduled daily email ingestion at {config.EMAIL_INGESTION_TIME}")
    except Exception as e:
        print(f"⚠️  Could not schedule email ingestion: {e}")
    
    # Schedule periodic email checks (every 30 minutes)
    try:
        scheduler.schedule_periodic_checks(interval_minutes=30)
    except Exception as e:
        print(f"⚠️  Could not schedule periodic email checks: {e}")


# Mount static files
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

