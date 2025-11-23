"""Script to initialize a new Gemini File Search Store."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.gemini_file_search import create_file_search_store


def main():
    """Create a new File Search Store."""
    print("Creating new Gemini File Search Store...")
    
    try:
        store_name = create_file_search_store("Denali School Store")
        print(f"\n✓ Success! Store created: {store_name}")
        print(f"\nPlease add this to your .env file:")
        print(f"FILE_SEARCH_STORE_NAME={store_name}")
        
    except Exception as e:
        print(f"\n✗ Error creating store: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

