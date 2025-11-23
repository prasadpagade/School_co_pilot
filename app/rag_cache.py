"""Caching system for RAG queries to improve performance and reduce costs."""
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.config import config


CACHE_FILE = "data/.rag_cache.json"
CACHE_EXPIRY_DAYS = 7  # Cache responses for 7 days


def get_cache_key(question: str) -> str:
    """Generate a cache key from the question."""
    # Normalize question: lowercase, strip whitespace
    normalized = question.lower().strip()
    # Generate hash
    return hashlib.md5(normalized.encode()).hexdigest()


def load_cache() -> Dict[str, Any]:
    """Load the cache from disk."""
    if not os.path.exists(CACHE_FILE):
        return {}
    
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_cache(cache: Dict[str, Any]) -> None:
    """Save the cache to disk."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def get_cached_response(question: str) -> Optional[str]:
    """
    Get a cached response for a question if it exists and hasn't expired.
    
    Args:
        question: The question to look up
        
    Returns:
        Cached answer if found and valid, None otherwise
    """
    cache = load_cache()
    cache_key = get_cache_key(question)
    
    if cache_key not in cache:
        return None
    
    cached_item = cache[cache_key]
    
    # Check expiry
    cached_time = datetime.fromisoformat(cached_item['timestamp'])
    expiry_time = cached_time + timedelta(days=CACHE_EXPIRY_DAYS)
    
    if datetime.now() > expiry_time:
        # Expired, remove from cache
        del cache[cache_key]
        save_cache(cache)
        return None
    
    return cached_item['answer']


def cache_response(question: str, answer: str) -> None:
    """
    Cache a question-answer pair.
    
    Args:
        question: The question asked
        answer: The answer received
    """
    cache = load_cache()
    cache_key = get_cache_key(question)
    
    cache[cache_key] = {
        'question': question,
        'answer': answer,
        'timestamp': datetime.now().isoformat()
    }
    
    # Clean up expired entries
    now = datetime.now()
    expired_keys = []
    for key, item in cache.items():
        cached_time = datetime.fromisoformat(item['timestamp'])
        expiry_time = cached_time + timedelta(days=CACHE_EXPIRY_DAYS)
        if now > expiry_time:
            expired_keys.append(key)
    
    for key in expired_keys:
        del cache[key]
    
    save_cache(cache)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    cache = load_cache()
    
    now = datetime.now()
    valid_count = 0
    expired_count = 0
    
    for item in cache.values():
        cached_time = datetime.fromisoformat(item['timestamp'])
        expiry_time = cached_time + timedelta(days=CACHE_EXPIRY_DAYS)
        if now > expiry_time:
            expired_count += 1
        else:
            valid_count += 1
    
    return {
        'total_entries': len(cache),
        'valid_entries': valid_count,
        'expired_entries': expired_count,
        'cache_file': CACHE_FILE
    }

