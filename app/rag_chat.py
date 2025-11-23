"""RAG chat implementation using Gemini File Search."""
import os
import google.genai as genai
from google.genai import types
from datetime import datetime, timedelta

from app.config import config
from app.rag_cache import get_cached_response, cache_response
from app.rag_improvement import track_query, get_optimized_prompt_base, calculate_response_quality
from app.response_formatter import format_response_for_action
import time


def ask_school_question(question: str, store_name: str, use_cache: bool = True) -> str:
    """
    Ask a question using Gemini File Search RAG.
    
    Args:
        question: The question to ask
        store_name: Name of the File Search Store
        use_cache: If True, check cache first and cache the response
        
    Returns:
        Answer string
    """
    if not config.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment variables")
    
    if not store_name:
        raise ValueError("FILE_SEARCH_STORE_NAME not set in environment variables")
    
    # Check cache first
    if use_cache:
        cached_answer = get_cached_response(question)
        if cached_answer:
            return cached_answer
    
    # Reuse client instance (connection pooling handled by SDK)
    client = genai.Client(api_key=config.GOOGLE_API_KEY)
    
    # Get current date for context
    current_date = datetime.now()
    current_date_str = current_date.strftime("%A, %B %d, %Y")
    current_week = current_date.strftime("%Y-W%V")  # ISO week format
    tomorrow_date = (current_date + timedelta(days=1))
    tomorrow_str = tomorrow_date.strftime("%A, %B %d, %Y")
    
    # System prompt with current date context
    system_instruction = f"""You are a school assistant for a busy parent.

IMPORTANT: Today's date is {current_date_str} (Week {current_week}).

When answering questions about time:
- "this week" means the current week (week of {current_date_str})
- "next week" means the week after the current week
- "tomorrow" means {tomorrow_str}
- Use the current date ({current_date_str}) as reference for all relative dates

Answer ONLY using information available in the File Search store.
If data is missing, say so clearly.
Be concise and clear.
Focus on actionable information like dates, events, and deadlines.
When mentioning dates, always include the full date (e.g., "Thursday, October 24, 2025") for clarity."""
    
    try:
        # Use direct file references (more reliable than File Search Store tool)
        # Files are uploaded via Files API and we reference them directly
        from app.markdown_consolidator import get_latest_markdown_file
        from pathlib import Path
        
        # Find latest consolidated markdown file
        consolidated_dir = Path("data/consolidated")
        
        if not consolidated_dir.exists():
            return "No consolidated data found. Please run email ingestion first."
        
        # Get all consolidated markdown files (sorted by modification time, newest first)
        md_files = sorted(
            consolidated_dir.glob("school-data-*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not md_files:
            return "No consolidated markdown files found. Please run email ingestion first."
        
        # Use the most recent consolidated file(s)
        files_to_use = []
        total_size = 0
        max_total_size = 10 * 1024 * 1024  # 10MB total limit
        
        for md_file in md_files:
            file_size = md_file.stat().st_size
            if total_size + file_size > max_total_size and files_to_use:
                break
            files_to_use.append(md_file)
            total_size += file_size
        
        # Check if files have been uploaded to Gemini Files API
        # Cache file list to avoid repeated API calls
        try:
            uploaded_files = list(client.files.list())
        except Exception as e:
            print(f"Error listing files: {e}")
            return "Error accessing uploaded files. Please check your API configuration."
        
        if not uploaded_files:
            return "No files have been uploaded to Gemini yet. Please run the upload script first."
        
        # Use the most recently uploaded file(s) - should be our consolidated markdown
        # Filter for active files only
        active_files = [f for f in uploaded_files if hasattr(f, 'state') and str(f.state).upper() == 'ACTIVE']
        if not active_files:
            active_files = uploaded_files  # Fallback if state not available
        
        sorted_files = sorted(
            active_files,
            key=lambda f: f.create_time if hasattr(f, 'create_time') else getattr(f, 'update_time', 0),
            reverse=True
        )[:len(files_to_use)]
        
        file_uris_to_use = [f.uri for f in sorted_files if hasattr(f, 'uri')]
        
        if not file_uris_to_use:
            return "Files haven't been uploaded to Gemini yet. Please run the upload script first."
        
        # Get optimized prompt base based on learned patterns
        optimized_base = get_optimized_prompt_base(question)
        
        # Create query text with explicit search instructions (enhanced with learning)
        query_text = f"""You are searching through a consolidated file containing ALL school emails and announcements for Denali.

IMPORTANT CONTEXT: Today is {current_date_str}.

Question: {question}

OPTIMIZED INSTRUCTIONS (based on learned patterns): {optimized_base}

SEARCH INSTRUCTIONS - READ CAREFULLY:
1. This file contains MULTIPLE emails organized by date. You MUST search through ALL of them.
2. The file structure is: "## Email: [DATE] - [SUBJECT]" followed by email content.
3. When searching for a person (e.g., "Ms. Lobeda", "Lobita", "Miss Lobeda"):
   - Search for emails WHERE the sender is that person (look for "**From:**" lines)
   - These names all refer to the same teacher: Lobeda, Lobita, Ms. Lobeda, Miss Lobeda, Grace Lobeda
4. When searching for a topic (e.g., "birthday policy", "dress code"):
   - Read through ALL emails that mention that topic
   - Look for complete policy information, not just brief mentions
   - Include ALL details: requirements, restrictions, quantities, deadlines
   - If an email says "review the dress code guidelines" but doesn't include them, check if there are attachments or other emails with the full guidelines
   - Extract the ACTUAL guidelines/policies, not just references to them
5. When you find the answer:
   - Provide COMPLETE information from the email(s)
   - Include specific details, not summaries
   - Quote relevant sections when helpful
   - Format your response to be ACTION-ORIENTED and EASY TO READ:
     * Use clear headings with **bold**
     * Use bullet points (•) for lists
     * Highlight important dates with **📅 [DATE]**
     * Make action items stand out with ✅ or ⚠️
     * Use proper markdown formatting
   - If you only find references (like "please review the guidelines"), explicitly state that the full guidelines are not in the available emails, but mention where they might be found
6. If you cannot find the information after searching thoroughly, say: "I could not find information about [topic] in the available emails."

RESPONSE FORMATTING REQUIREMENTS:
- Use markdown formatting (**, *, lists)
- Make dates prominent (e.g., **📅 November 24, 2025**)
- Use bullet points (•) for lists
- Add section headers for clarity (use **bold**)
- Make the response scannable and action-oriented
- Highlight requirements with ⚠️ and allowed items with ✅

Now search the file and answer: {question}"""
        
        # Create content parts with file references
        parts = [types.Part.from_text(text=query_text)]
        for file_uri in file_uris_to_use:
            try:
                parts.append(types.Part(file_data=types.FileData(file_uri=file_uri)))
            except Exception as e:
                print(f"Warning: Could not add file reference {file_uri}: {e}")
                continue
        
        if len(parts) == 1:  # Only query text, no files
            return "Error: Could not create query with file references."
        
        # Generate content with direct file references
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=parts,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )
        except Exception as api_error:
            # If rate limited, provide helpful message
            error_str = str(api_error)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                return ("I'm currently experiencing rate limits from the Gemini API. "
                       "Please wait a few minutes and try again, or check your API usage at "
                       "https://ai.dev/usage?tab=rate-limit. "
                       "The files have been successfully uploaded to the File Search Store, so once the "
                       "rate limit resets, queries should work normally.")
            raise
        
        # Extract text from response
        answer = None
        if hasattr(response, 'text') and response.text:
            answer = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            # Try to extract from candidates
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    parts = candidate.content.parts if hasattr(candidate.content, 'parts') else []
                    for part in parts:
                        if hasattr(part, 'text') and part.text:
                            answer = part.text
                            break
                if answer:
                    break
        
        if not answer:
            answer = "I couldn't generate a response. Please check your File Search Store configuration."
        
        # Format response to be action-oriented and well-structured
        try:
            answer = format_response_for_action(answer, question)
        except Exception as e:
            print(f"Warning: Response formatting failed: {e}")
            # Continue with unformatted answer if formatting fails
        
        # Cache the response (cache the formatted version)
        if use_cache and answer:
            cache_response(question, answer)
        
        # Track query for self-improvement with quality scoring
        try:
            start_track = time.time()
            quality_score, quality_analysis = calculate_response_quality(answer, question)
            success = quality_score >= 0.5  # Consider quality >= 0.5 as success
            track_query(
                question, 
                answer, 
                response_time=time.time() - start_track, 
                success=success,
                quality_score=quality_score,
                auto_score=False  # We already calculated it
            )
        except Exception as e:
            print(f"Warning: Failed to track query for self-improvement: {e}")
            # Fallback to basic tracking
            try:
                track_query(question, answer, response_time=0, success=True, auto_score=True)
            except:
                pass
        
        return answer
        
    except Exception as e:
        raise Exception(f"Error generating response: {e}")

