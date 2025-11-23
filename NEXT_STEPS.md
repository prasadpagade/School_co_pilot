# 🚀 Next Steps: RAG Architecture Refactor

## ✅ What's Done

- Master markdown consolidation system implemented
- Attachment transcription (PDFs, images → text)
- Weekly file splitting with size limits
- Automatic cleanup of temporary files
- Single file upload instead of 238 files

---

## 📋 Immediate Next Steps

### Step 1: Test Email Ingestion with New System ⭐ PRIORITY

**Test the consolidation flow:**

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run email ingestion (this will use new consolidation)
python -m app.ingest_emails
```

**What to check:**
- ✅ New emails are fetched from Gmail
- ✅ Attachments are saved temporarily
- ✅ PDFs/images are transcribed to text
- ✅ Email + attachments are consolidated into `data/consolidated/school-data-YYYY-WWW.md`
- ✅ Temporary attachment files are deleted after consolidation
- ✅ Markdown file is properly formatted

**Expected output:**
```
📧 Processing email: [Subject]
  📎 Saved attachment: [filename]
  📄 Processing PDF: [filename]
  ✓ Extracted [X] characters from PDF
  ✓ Consolidated email into: school-data-2025-W47.md
🧹 Cleaning up temporary files...
  ✓ Deleted [X] temporary attachment files
```

---

### Step 2: Verify Markdown File Structure

**Check the consolidated file:**

```bash
# View the consolidated markdown file
cat data/consolidated/school-data-*.md | head -100

# Or open in editor
code data/consolidated/school-data-*.md
```

**What to verify:**
- ✅ Email headers (From, Date, Subject)
- ✅ Email body text is preserved
- ✅ Attachments section exists
- ✅ PDF/image text is transcribed correctly
- ✅ Markdown formatting is clean

---

### Step 3: Upload Consolidated File to Gemini

**Upload the consolidated markdown:**

```bash
# Use the updated backfill script
python -m scripts.backfill_emails
```

**What to check:**
- ✅ Markdown file is found
- ✅ File uploads successfully to Gemini
- ✅ No errors during upload
- ✅ File is marked as uploaded (won't re-upload)

**Expected output:**
```
📄 Uploading: school-data-2025-W47.md
  ✓ Successfully uploaded: school-data-2025-W47.md
```

---

### Step 4: Test RAG Queries with Consolidated File

**Test the RAG system:**

```bash
# Start the API server
uvicorn app.main:app --reload

# In another terminal, test a query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What events are happening this week?"}'
```

**Or use the web UI:**
1. Open http://localhost:8000
2. Ask questions in the chat interface
3. Verify responses use information from consolidated file

**What to check:**
- ✅ RAG finds the consolidated markdown file
- ✅ Queries return accurate information
- ✅ All email content is searchable
- ✅ Attachments (PDFs/images) content is included in answers
- ✅ No "No files uploaded" errors

---

### Step 5: Migration - Consolidate Existing Data (Optional)

**If you have existing 238 files, consolidate them:**

**Option A: Fresh Start (Recommended)**
- Keep old files as backup: `cp -r data/ data_backup/`
- Run new ingestion: `python -m app.ingest_emails`
- New emails will be consolidated automatically
- Old files can be deleted after verification

**Option B: Migrate Existing Files**
- Create migration script to consolidate existing emails/attachments
- Transcribe existing PDFs/images
- Generate consolidated markdown from old data

**Recommendation**: Start fresh with new emails. The new system will work going forward.

---

## 🔍 Testing Checklist

### Email Ingestion
- [ ] New emails are fetched correctly
- [ ] PDF attachments are transcribed
- [ ] Image attachments are transcribed
- [ ] Email content is preserved
- [ ] Markdown file is created/updated
- [ ] Temporary files are cleaned up

### File Management
- [ ] Weekly files are created correctly (`school-data-YYYY-WWW.md`)
- [ ] Files append to current week's file
- [ ] Size limit splitting works (>5MB creates new part)
- [ ] No duplicate content

### Upload
- [ ] Consolidated markdown uploads to Gemini
- [ ] Upload tracker prevents duplicates
- [ ] Upload succeeds without errors

### RAG Queries
- [ ] RAG finds consolidated markdown file(s)
- [ ] Queries return accurate answers
- [ ] All email content is searchable
- [ ] Attachments content is included
- [ ] Date context works correctly

### Cleanup
- [ ] Old raw email files can be deleted
- [ ] Old attachment files can be deleted
- [ ] Consolidated markdown files are kept

---

## 🐛 Potential Issues & Solutions

### Issue 1: "No consolidated markdown file found"
**Solution**: Run email ingestion first:
```bash
python -m app.ingest_emails
```

### Issue 2: PDF transcription fails
**Solution**: 
- Check API key is set: `echo $GOOGLE_API_KEY`
- Check PDF file size (may need to split large PDFs)
- Check API rate limits

### Issue 3: Upload fails
**Solution**:
- Verify `FILE_SEARCH_STORE_NAME` is set in `.env`
- Check file exists: `ls -la data/consolidated/`
- Check Gemini API limits

### Issue 4: RAG can't find uploaded file
**Solution**:
- Verify file was uploaded: Check Gemini console
- Check filename matching logic in `rag_chat.py`
- Try re-uploading the file

### Issue 5: Storage still filling up
**Solution**:
- Delete old raw files: `rm -rf data/raw_emails/*`
- Delete old attachments: `rm -rf data/attachments/*`
- Keep only consolidated markdown files

---

## 📊 Performance Verification

### Before vs After Comparison

**Before (Old System):**
```bash
# Count files
find data/raw_emails -type f | wc -l  # ~134 files
find data/attachments -type f | wc -l  # ~104 files
du -sh data/raw_emails data/attachments  # ~50MB

# Upload time
time python -m scripts.backfill_emails  # ~5-10 minutes
```

**After (New System):**
```bash
# Count files
find data/consolidated -type f | wc -l  # ~1-2 files (weekly)
du -sh data/consolidated  # ~5MB

# Upload time
time python -m scripts.backfill_emails  # ~30 seconds
```

**Expected improvements:**
- ✅ 99% fewer files (1-2 vs 238)
- ✅ 90% less storage (5MB vs 50MB)
- ✅ 95% faster uploads (30s vs 5-10min)
- ✅ 100% context available (vs 4% with 10 files)

---

## 🎯 Recommended Testing Order

1. **Test with 1-2 new emails** (if available)
   - Verify consolidation works
   - Check markdown format
   - Test upload

2. **Test with existing emails** (if needed)
   - Run ingestion on existing data
   - Verify transcription quality
   - Test RAG queries

3. **Verify RAG quality**
   - Ask questions about recent emails
   - Check if attachments are searchable
   - Verify date context works

4. **Cleanup old files** (after verification)
   - Backup old data
   - Delete raw emails/attachments
   - Keep only consolidated markdown

---

## 🔄 Daily/Weekly Workflow

### Daily Ingestion (Scheduled at 6pm)
```bash
# Automated via scheduler
python -m app.ingest_emails
# - Fetches new emails
# - Appends to current week's markdown file
# - Uploads updated file if new content
# - Cleans up temp files
```

### Manual Upload (If needed)
```bash
# Upload latest consolidated file
python -m scripts.backfill_emails
```

### Manual Cleanup (Optional)
```bash
# Delete old raw files after upload
rm -rf data/raw_emails/*
rm -rf data/attachments/*
```

---

## 📝 Monitoring

### Check Markdown File Status
```bash
# List consolidated files
ls -lh data/consolidated/

# Check file size
du -sh data/consolidated/*

# View latest file
tail -50 data/consolidated/school-data-*.md | head -1
```

### Check Upload Status
```bash
# Check if files are marked as uploaded
cat data/.upload_tracker.json | jq
```

### Check RAG Cache
```bash
# View cache stats
curl http://localhost:8000/cache/stats
```

---

## ✅ Success Criteria

**System is working correctly if:**
- ✅ New emails append to markdown file
- ✅ Attachments are transcribed successfully
- ✅ Markdown file uploads to Gemini
- ✅ RAG queries return accurate information
- ✅ Storage usage is minimal (only markdown files)
- ✅ No duplicate uploads
- ✅ Cleanup removes temporary files

---

## 🆘 Need Help?

### Debug Mode
Enable verbose logging in ingestion:
```python
# In app/ingest_emails.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs
```bash
# Check for errors in ingestion
python -m app.ingest_emails 2>&1 | tee ingestion.log

# Check for errors in upload
python -m scripts.backfill_emails 2>&1 | tee upload.log
```

### Verify Configuration
```bash
# Check environment variables
cat .env | grep -E "(GOOGLE_API_KEY|FILE_SEARCH_STORE_NAME)"
```

---

## 🎉 Ready to Start?

**Begin with Step 1** - Test email ingestion:
```bash
source .venv/bin/activate
python -m app.ingest_emails
```

**Then proceed through each step**, checking the boxes as you go!

Good luck! 🚀

