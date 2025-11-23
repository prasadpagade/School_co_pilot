# 🔧 RAG Fix Plan - Critical Issues

## ❌ Problems Identified

1. **Files uploaded but NOT added to File Search Store**
   - Files are uploaded to Files API
   - But NOT explicitly added to File Search Store
   - RAG can't find them because they're not in the store

2. **RAG using wrong approach**
   - Currently using direct file URIs
   - Should use File Search Store tool for semantic search
   - File Search Store does better semantic matching

3. **Test script marking wrong answers as "passed"**
   - Need better validation logic

## ✅ Fixes Applied

### 1. Explicitly Add Files to File Search Store
- Modified `upload_file_to_store()` to call `addFiles` API
- Files are now added to store after upload

### 2. Use File Search Store Tool
- Changed RAG to use `Tool.from_file_search()` instead of direct file URIs
- This enables semantic search across all files in store

### 3. Improved Test Validation
- Better logic to detect wrong answers
- Checks for topic relevance, not just "not found" messages

## 🔄 Next Steps

1. **Clear upload tracker** (to force re-upload):
   ```bash
   rm data/.upload_tracker.json
   ```

2. **Re-upload consolidated file**:
   ```bash
   python -m scripts.backfill_emails
   ```
   This will:
   - Upload file to Files API
   - Add file to File Search Store (NEW!)
   - Wait for processing

3. **Restart server**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Test again**:
   ```bash
   python test_rag_queries.py
   ```

## 🎯 Expected Results

After fixes:
- ✅ "What is the birthday policy from Ms. Lobeda?" → Should find birthday email
- ✅ "What are the dress code guidelines?" → Should find dress code info
- ✅ "What treats can be brought for birthdays?" → Should find treat requirements

## 📊 Self-Improvement Metrics

The system now tracks:
- Query success/failure rates
- Response times
- Common questions
- Query type distribution
- Improvement suggestions

Access via: `GET /rag/metrics`

