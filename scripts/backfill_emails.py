"""Script to backfill emails, consolidate into markdown, and upload to Gemini File Search Store."""
import sys
import subprocess
from pathlib import Path
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config
from app.gemini_file_search import upload_consolidated_markdown, cleanup_old_files
from app.markdown_consolidator import get_latest_markdown_file


def main():
    """Backfill emails, consolidate into markdown, upload, and cleanup."""
    print("Starting backfill process...")
    print("="*80)
    print("NEW ARCHITECTURE: Emails + attachments → Consolidated Markdown → Upload → Cleanup")
    print("="*80)
    
    # Check if store is configured
    if not config.FILE_SEARCH_STORE_NAME:
        print("ERROR: FILE_SEARCH_STORE_NAME not set in .env")
        print("Please run: python -m scripts.init_file_search_store")
        sys.exit(1)
    
    # Step 1: Ingest emails (now consolidates into markdown automatically)
    print("\n" + "="*80)
    print("Step 1: Ingesting emails and consolidating into markdown...")
    print("="*80)
    try:
        subprocess.run([sys.executable, "-m", "app.ingest_emails"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error ingesting emails: {e}")
        sys.exit(1)
    
    # Step 2: Upload consolidated markdown file(s)
    print("\n" + "="*80)
    print("Step 2: Uploading consolidated markdown file(s) to File Search Store...")
    print("="*80)
    
    consolidated_dir = Path("data/consolidated")
    if not consolidated_dir.exists():
        print("ERROR: No consolidated markdown files found. Check ingestion step.")
        sys.exit(1)
    
    # Find all consolidated markdown files
    md_files = sorted(
        consolidated_dir.glob("school-data-*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True  # Upload newest first
    )
    
    if not md_files:
        print("ERROR: No consolidated markdown files found.")
        sys.exit(1)
    
    uploaded_count = 0
    for md_file in md_files:
        try:
            print(f"\n📄 Uploading: {md_file.name}")
            file_uri = upload_consolidated_markdown(
                store_name=config.FILE_SEARCH_STORE_NAME,
                markdown_path=str(md_file)
            )
            if file_uri:
                uploaded_count += 1
                print(f"  ✓ Successfully uploaded: {md_file.name}")
            else:
                print(f"  ⊘ Skipped (already uploaded): {md_file.name}")
        except Exception as e:
            print(f"  ✗ Error uploading {md_file.name}: {e}")
    
    # Step 3: Cleanup old files (optional - only if upload succeeded)
    if uploaded_count > 0:
        print("\n" + "="*80)
        print("Step 3: Cleaning up old raw files (optional)...")
        print("="*80)
        print("Note: Old email/attachment files can be deleted after successful upload.")
        print("This saves storage space and removes PII from disk.")
        
        cleanup = input("\nDelete old raw email and attachment files? (y/N): ").strip().lower()
        if cleanup == 'y':
            stats = cleanup_old_files(keep_markdown=True)
            print(f"\n✓ Cleanup complete:")
            print(f"  - Deleted {stats['emails_deleted']} old email files")
            print(f"  - Deleted {stats['attachments_deleted']} old attachment files")
            if stats['errors'] > 0:
                print(f"  - {stats['errors']} errors during cleanup")
        else:
            print("Skipping cleanup. Files kept for backup.")
    
    # Summary
    print("\n" + "="*80)
    print("✅ Backfill complete!")
    print("="*80)
    print(f"  - Consolidated emails into {len(md_files)} markdown file(s)")
    print(f"  - Uploaded {uploaded_count} markdown file(s) to File Search Store")
    print(f"  - Files: {', '.join([f.name for f in md_files])}")
    print(f"\nStore: {config.FILE_SEARCH_STORE_NAME}")
    print("\nYou can now start the API server:")
    print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()

