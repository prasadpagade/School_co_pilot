"""Gemini File Search operations for uploading and managing files."""
import os
import time
import json
import requests
from pathlib import Path
from typing import Optional, Set

import google.genai as genai
from google.genai import types

from app.config import config
from app.upload_tracker import is_file_uploaded, mark_file_uploaded


def initialize_client() -> genai.Client:
    """Initialize Gemini client with API key."""
    if not config.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment variables")
    
    return genai.Client(api_key=config.GOOGLE_API_KEY)


def create_file_search_store(display_name: str) -> str:
    """
    Create a new File Search Store using REST API.
    
    Args:
        display_name: Human-readable name for the store
        
    Returns:
        Store name (e.g., "fileSearchStores/denali-school-store-123")
    """
    if not config.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not set in environment variables")
    
    url = "https://generativelanguage.googleapis.com/v1beta/fileSearchStores"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": config.GOOGLE_API_KEY
    }
    payload = {
        "displayName": display_name
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        store_data = response.json()
        store_name = store_data.get("name")
        
        if not store_name:
            raise Exception(f"Store creation response missing 'name': {store_data}")
        
        print(f"Created File Search Store: {store_name}")
        return store_name
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error creating file search store: {e}")


def upload_file_to_store(filepath: str, store_name: str, skip_if_exists: bool = True) -> Optional[str]:
    """
    Upload a single file to Gemini Files API.
    This uses the Files API which is more reliable and works with direct file references.
    
    Args:
        filepath: Path to the file to upload
        store_name: Name of the File Search Store (kept for compatibility, but not used)
        skip_if_exists: If True, skip files that have already been uploaded
        
    Returns:
        File URI (name), or None if skipped
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Check if already uploaded
    if skip_if_exists and is_file_uploaded(filepath):
        print(f"  ⊘ Skipped (already uploaded): {os.path.basename(filepath)}")
        return None
    
    client = initialize_client()
    
    try:
        # Upload file - for markdown files, temporarily rename to .txt
        # since Gemini SDK handles .txt files better
        print(f"Uploading {filepath}...")
        
        file_ext = Path(filepath).suffix.lower()
        temp_filepath = filepath
        
        # If markdown file, create temporary .txt copy for upload
        if file_ext == '.md':
            temp_filepath = filepath.replace('.md', '.txt')
            import shutil
            shutil.copy2(filepath, temp_filepath)
            print(f"  📝 Created temporary .txt copy for upload: {os.path.basename(temp_filepath)}")
        
        # Upload using SDK (it will auto-detect text/plain for .txt files)
        file = client.files.upload(path=temp_filepath)
        
        # Clean up temporary file if we created one
        if temp_filepath != filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
            print(f"  🧹 Cleaned up temporary file")
        
        # Wait for file to be processed
        max_wait = 120  # 2 minutes max
        wait_time = 0
        print(f"  ⏳ Waiting for file to process... (max {max_wait}s)")
        
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
            time.sleep(5)
            wait_time += 5
            file = client.files.get(name=file.name)
            state = get_state_string(file.state)
            if wait_time % 15 == 0:
                print(f"  ⏳ Still processing... ({wait_time}s/{max_wait}s)")
        
        state = get_state_string(file.state)
        if "PROCESSING" in state:
            print(f"  ⚠️  File still processing after {max_wait}s. It will continue in background.")
            print(f"  ✓ File uploaded (still processing): {os.path.basename(filepath)} (name: {file.name})")
            mark_file_uploaded(filepath)
            return file.name
        elif "ACTIVE" not in state:
            raise Exception(f"File upload failed. State: {state}")
        
        print(f"  ✓ Uploaded: {os.path.basename(filepath)} (name: {file.name})")
        
        # Mark as uploaded
        mark_file_uploaded(filepath)
        
        return file.name
        
    except Exception as e:
        raise Exception(f"Error uploading file {filepath}: {e}")


def bulk_upload_directory(dir_path: str, store_name: str) -> int:
    """
    Upload all files from a directory to the File Search Store.
    
    Args:
        dir_path: Directory containing files to upload
        store_name: Name of the File Search Store
        
    Returns:
        Number of files uploaded
    """
    if not os.path.exists(dir_path):
        print(f"Directory not found: {dir_path}")
        return 0
    
    if not store_name:
        raise ValueError("FILE_SEARCH_STORE_NAME not set in environment variables")
    
    # Get all files in directory
    files = []
    for root, dirs, filenames in os.walk(dir_path):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            # Skip hidden files and directories
            if not filename.startswith('.'):
                files.append(filepath)
    
    if not files:
        print(f"No files found in {dir_path}")
        return 0
    
    print(f"Found {len(files)} files in {dir_path}...")
    
    uploaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    for filepath in files:
        try:
            result = upload_file_to_store(filepath, store_name, skip_if_exists=True)
            if result is None:
                skipped_count += 1
            else:
                uploaded_count += 1
        except Exception as e:
            print(f"  ✗ Failed to upload {filepath}: {e}")
            failed_count += 1
    
    print(f"\nUpload complete: {uploaded_count} new, {skipped_count} skipped, {failed_count} failed")
    return uploaded_count


def list_files_in_store(store_name: str) -> list:
    """
    List all files in a File Search Store.
    
    Args:
        store_name: Name of the File Search Store
        
    Returns:
        List of file URIs
    """
    client = initialize_client()
    
    try:
        store = client.file_search_stores.get(name=store_name)
        return store.file_uris if hasattr(store, 'file_uris') else []
    except Exception as e:
        print(f"Error listing files in store: {e}")
        return []


def upload_consolidated_markdown(store_name: str, markdown_path: Optional[str] = None) -> Optional[str]:
    """
    Upload the consolidated markdown file to File Search Store.
    If markdown_path is not provided, finds the latest consolidated file.
    
    Args:
        store_name: Name of the File Search Store
        markdown_path: Optional path to markdown file. If None, finds latest.
        
    Returns:
        File URI, or None if skipped
    """
    from app.markdown_consolidator import get_latest_markdown_file
    
    # Find markdown file if not provided
    if not markdown_path:
        md_file = get_latest_markdown_file()
        if not md_file:
            print("⚠️  No consolidated markdown file found. Run ingestion first.")
            return None
        markdown_path = str(md_file)
    
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
    
    # Check if already uploaded (by file path)
    if is_file_uploaded(markdown_path):
        print(f"  ⊘ Skipped (already uploaded): {os.path.basename(markdown_path)}")
        return None
    
    # Upload the consolidated file
    return upload_file_to_store(markdown_path, store_name, skip_if_exists=True)


def cleanup_old_files(keep_markdown: bool = True) -> dict:
    """
    Clean up old raw email and attachment files after consolidation.
    
    Args:
        keep_markdown: If True, keep the consolidated markdown files
        
    Returns:
        Dict with cleanup statistics
    """
    from pathlib import Path
    
    stats = {
        'emails_deleted': 0,
        'attachments_deleted': 0,
        'errors': 0
    }
    
    # Clean up raw emails directory
    if os.path.exists(config.RAW_EMAILS_DIR):
        for file_path in Path(config.RAW_EMAILS_DIR).rglob('*'):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    stats['emails_deleted'] += 1
                except Exception as e:
                    print(f"  ⚠️  Could not delete {file_path}: {e}")
                    stats['errors'] += 1
    
    # Clean up attachments directory
    if os.path.exists(config.ATTACHMENTS_DIR):
        for file_path in Path(config.ATTACHMENTS_DIR).rglob('*'):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    stats['attachments_deleted'] += 1
                except Exception as e:
                    print(f"  ⚠️  Could not delete {file_path}: {e}")
                    stats['errors'] += 1
    
    return stats

