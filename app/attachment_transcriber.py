"""Transcribe attachments (PDFs, images) to text for RAG."""
import os
import time
from pathlib import Path
from typing import Optional
from google.genai import types
from google.genai.types import FileState

from app.config import config
from app.gemini_file_search import initialize_client
from app.image_processor import extract_text_from_image


def transcribe_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using Gemini Vision API.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    if not config.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment variables")
    
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    client = initialize_client()
    
    try:
        # Upload PDF to Gemini Files API
        print(f"  📄 Processing PDF: {os.path.basename(pdf_path)}")
        file = client.files.upload(path=pdf_path)
        
        # Wait for file to be processed
        max_wait = 60  # PDFs may take longer to process
        wait_time = 0
        
        # Get state - handle both string and object types
        def get_state_string(state):
            if isinstance(state, str):
                return state.upper()
            elif hasattr(state, 'name'):
                return state.name.upper()
            else:
                return str(state).upper()
        
        state = get_state_string(file.state)
        while "PROCESSING" in state and wait_time < max_wait:
            time.sleep(2)
            wait_time += 2
            file = client.files.get(name=file.name)
            state = get_state_string(file.state)
        
        state = get_state_string(file.state)
        if "ACTIVE" not in state:
            raise Exception(f"PDF upload failed. State: {state}")
        
        # Use Gemini to extract text from PDF
        prompt = """Extract ALL text from this PDF document with high accuracy.
        
CRITICAL INSTRUCTIONS:
- Extract ALL text content, preserving structure and formatting where possible
- Include ALL dates, times, events, and important information
- Preserve lists, bullet points, and structured data
- Extract headers and section titles
- Include all contact information, deadlines, and action items
- Do not summarize - extract the complete text content

Extract the text EXACTLY as it appears in the document."""
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                types.Part.from_text(text=prompt),
                types.Part(file_data=types.FileData(file_uri=file.uri))
            ],
            config=types.GenerateContentConfig(
                temperature=0.1
            )
        )
        
        extracted_text = None
        
        if hasattr(response, 'text') and response.text:
            extracted_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    parts = candidate.content.parts if hasattr(candidate.content, 'parts') else []
                    for part in parts:
                        if hasattr(part, 'text') and part.text:
                            extracted_text = part.text
                            break
                if extracted_text:
                    break
        
        if not extracted_text:
            raise Exception("Could not extract text from PDF. The PDF may be scanned images or empty.")
        
        print(f"  ✓ Extracted {len(extracted_text)} characters from PDF")
        return extracted_text
    
    except Exception as e:
        raise Exception(f"Error processing PDF {pdf_path}: {e}")


def transcribe_image(image_path: str) -> str:
    """
    Extract text from image using existing OCR functionality.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text from the image
    """
    return extract_text_from_image(image_path)


def transcribe_attachment(attachment_path: str, mime_type: Optional[str] = None) -> str:
    """
    Transcribe an attachment based on its file type.
    
    Args:
        attachment_path: Path to the attachment file
        mime_type: Optional MIME type of the attachment
        
    Returns:
        Extracted text from the attachment
    """
    if not Path(attachment_path).exists():
        raise FileNotFoundError(f"Attachment not found: {attachment_path}")
    
    # Determine file type from extension or MIME type
    ext = Path(attachment_path).suffix.lower()
    
    # Image types
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        print(f"  🖼️  Processing image: {os.path.basename(attachment_path)}")
        return transcribe_image(attachment_path)
    
    # PDF
    elif ext == '.pdf':
        return transcribe_pdf(attachment_path)
    
    # Text files
    elif ext in ['.txt', '.md', '.csv']:
        print(f"  📝 Reading text file: {os.path.basename(attachment_path)}")
        with open(attachment_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    # Unsupported type
    else:
        print(f"  ⚠️  Unsupported file type: {ext} ({attachment_path})")
        return f"[Attachment: {os.path.basename(attachment_path)} - File type not supported for transcription]"

