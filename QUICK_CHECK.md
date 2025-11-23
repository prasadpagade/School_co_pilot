# ✅ Quick Verification Checklist

## Step 1: Test Email Ingestion & Consolidation

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run email ingestion (this consolidates into markdown)
python -m app.ingest_emails
```

**What to check:**
- ✅ Script runs without errors
- ✅ New emails are fetched from Gmail
- ✅ See messages like: "📧 Processing email: [Subject]"
- ✅ See: "📄 Processing PDF: [filename]" (if attachments exist)
- ✅ See: "✓ Consolidated email into: school-data-YYYY-WWW.md"
- ✅ See: "✓ Deleted [X] temporary attachment files"

**Expected output:**
```
Starting email ingestion...
Found X school-related emails

📧 Processing email: [Subject]
  📎 Saved attachment: [filename]
  📄 Processing PDF: [filename]
  ✓ Extracted [X] characters from PDF
  ✓ Consolidated email into: school-data-2025-W47.md
🧹 Cleaning up temporary files...
  ✓ Deleted [X] temporary attachment files

✅ Ingestion complete!
  - Consolidated X new emails into master markdown
```

---

## Step 2: Verify Markdown File Was Created

```bash
# Check consolidated directory exists
ls -la data/consolidated/

# View the markdown file
cat data/consolidated/school-data-*.md | head -50
```

**What to check:**
- ✅ `data/consolidated/` directory exists
- ✅ File named `school-data-YYYY-WWW.md` exists (current week)
- ✅ File contains email headers (From, Date, Subject)
- ✅ File contains email body text
- ✅ If attachments exist, see "### Attachments:" section
- ✅ Transcribed attachment content is present

**Expected structure:**
```markdown
# School Emails & Announcements
**Generated:** 2025-11-20 18:00:00
**Week:** 2025-W47

---

## Email: 2025-11-20 - [Subject]
**From:** [Sender]
**Date:** 2025-11-20 08:30:00
**Email ID:** [ID]

[Email body text...]

### Attachments:
#### [filename].pdf
[Transcribed PDF content...]

---
```

---

## Step 3: Upload Consolidated File to Gemini

```bash
# Upload the consolidated markdown file
python -m scripts.backfill_emails
```

**What to check:**
- ✅ Script finds the consolidated markdown file
- ✅ See: "📄 Uploading: school-data-YYYY-WWW.md"
- ✅ See: "✓ Successfully uploaded: school-data-YYYY-WWW.md"
- ✅ No errors during upload

**Expected output:**
```
Step 2: Uploading consolidated markdown file(s) to File Search Store...

📄 Uploading: school-data-2025-W47.md
  ✓ Successfully uploaded: school-data-2025-W47.md

✅ Backfill complete!
  - Consolidated emails into 1 markdown file(s)
  - Uploaded 1 markdown file(s) to File Search Store
```

---

## Step 4: Test RAG Queries

```bash
# Start the API server
uvicorn app.main:app --reload
```

**Then open in browser:**
- Go to: http://localhost:8000
- Ask questions in the chat interface

**Test queries:**
1. "What events are happening this week?"
2. "Tell me about the latest email from Miss Lobeda"
3. "What's in the field trip permission slip?" (if you have PDF attachments)

**What to check:**
- ✅ Chat interface loads
- ✅ Questions return answers (not "No files uploaded")
- ✅ Answers contain information from your emails
- ✅ If you have attachments, their content is searchable
- ✅ Dates are formatted correctly

**Expected behavior:**
- RAG finds the consolidated markdown file
- Returns specific information from your emails
- Includes details from attachments if asked

---

## Step 5: Verify Old Data Can Be Deleted (Optional)

**Only after confirming everything works:**

```bash
# Check file sizes
du -sh data/raw_emails data/attachments data/consolidated

# If consolidated markdown exists and is working:
rm -rf data/raw_emails data/attachments

# Verify cleanup
ls -la data/
# Should only show: consolidated/
```

**What to check:**
- ✅ Consolidated markdown file exists and contains all data
- ✅ RAG queries still work after deleting old files
- ✅ Storage usage is much smaller

---

## 🐛 Troubleshooting

### Issue: "No consolidated markdown file found"
**Solution:** Run Step 1 first (email ingestion)

### Issue: "No files have been uploaded yet"
**Solution:** Run Step 3 (upload consolidated file)

### Issue: PDF transcription fails
**Solution:** 
- Check API key: `echo $GOOGLE_API_KEY`
- Check API rate limits
- Large PDFs may need more time

### Issue: Upload fails
**Solution:**
- Check `FILE_SEARCH_STORE_NAME` in `.env`
- Verify store exists in Gemini console

### Issue: RAG can't find file
**Solution:**
- Verify file was uploaded in Gemini console
- Check file name matches in `rag_chat.py`
- Try re-uploading

---

## ✅ Success Criteria

**Everything is working if:**
- ✅ New emails append to markdown file
- ✅ Attachments are transcribed successfully  
- ✅ Markdown file uploads to Gemini
- ✅ RAG queries return accurate information
- ✅ Storage usage is minimal (only markdown files)

---

## 🚀 Quick Command Sequence

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Ingest & consolidate
python -m app.ingest_emails

# 3. Upload consolidated file
python -m scripts.backfill_emails

# 4. Start server & test
uvicorn app.main:app --reload
# Then open http://localhost:8000
```

**That's it!** 🎉

