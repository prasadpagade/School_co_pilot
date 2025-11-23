"""Process images to extract text using Gemini Vision API."""
import base64
from typing import Optional
from pathlib import Path

from app.config import config
from app.gemini_file_search import initialize_client
from google.genai import types


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using Gemini Vision API.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text from the image
    """
    if not config.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment variables")
    
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    client = initialize_client()
    
    try:
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Upload image to Gemini Files API
        file = client.files.upload(path=image_path)
        
        # Wait for file to be processed
        import time
        max_wait = 30
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
            raise Exception(f"Image upload failed. State: {state}")
        
        # Use Gemini to extract text from image
        prompt = """Extract ALL text from this image with high accuracy. 
If this is a conversation (SMS, WhatsApp, iMessage, etc.), extract the COMPLETE conversation including:
- ALL messages from all participants
- ALL dates mentioned (including formats like "Nov 18,20", "Dec 2,4,9,11")
- ALL times mentioned (including formats like "345-445" which means 3:45-4:45 PM, or "530-630" which means 5:30-6:30 PM)
- ALL events mentioned (classes, concerts, meetings, etc.)
- ALL locations mentioned
- ALL important details (dress code, requirements, etc.)

CRITICAL: Extract the text EXACTLY as it appears. Do not summarize or skip any information.
Preserve the conversation structure and include all dates, times, and event names."""
        
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
            raise Exception("Could not extract text from image. The image may be unclear or contain no readable text.")
        
        # Log extracted text for debugging (first 200 chars)
        print(f"📸 Extracted text (first 200 chars): {extracted_text[:200]}...")
        
        return extracted_text
    
    except Exception as e:
        raise Exception(f"Error processing image: {e}")

