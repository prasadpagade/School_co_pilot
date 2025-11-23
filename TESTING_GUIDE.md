# 🧪 Testing Guide - Denali School Copilot

## Quick Start Testing

### 1. Start the Server
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Open the UI
Navigate to: **http://127.0.0.1:8000**

---

## ✅ Feature Testing Checklist

### Core Features

#### 1. **RAG Chatbot** ✅
**Test:**
- Open http://127.0.0.1:8000
- Ask: "What events are happening at school this week?"
- Ask: "When is the next field trip?"
- Ask: "What are the latest school announcements?"

**Expected:**
- Responses based on uploaded emails
- Markdown formatting (bold, lists)
- Fast response if cached

**API Test:**
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What events are happening this week?"}'
```

---

#### 2. **Voice Input** ✅
**Test:**
- Click microphone button
- Allow microphone access
- Say: "What events are happening this week?"
- Should auto-fill and send

**Expected:**
- Button turns red when recording
- Shows "Listening..." status
- Auto-sends after speech recognition

---

#### 3. **Image Upload & Date Extraction** ✅
**Test:**
- Go to Calendar tab
- Click "Choose Image"
- Upload a screenshot of a conversation with dates
- Wait for processing

**Expected:**
- Extracts dates from image
- Shows extracted events
- Option to add to calendar

**API Test:**
```bash
curl -X POST http://127.0.0.1:8000/process-conversation-image \
  -F "file=@/path/to/image.jpg" \
  -F "attendees=wife@example.com"
```

---

#### 4. **Calendar Event Creation** ✅
**Test:**
- After extracting dates from image
- Click "Add to Calendar" for an event
- Check your Google Calendar

**Expected:**
- Event created in calendar
- Attendees invited (if configured)
- Reminder set (60 minutes before)

**API Test:**
```bash
curl -X POST http://127.0.0.1:8000/create-calendar-event \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Music class",
    "date": "2025-12-15",
    "time": "15:00",
    "description": "Music class for Denali",
    "attendees": ["wife@example.com"]
  }'
```

---

#### 5. **Scheduled Email Ingestion** ✅
**Test:**
- Go to Schedule tab
- Check status display
- Verify next run time

**Expected:**
- Shows "Active" status
- Shows ingestion time (default: 18:00)
- Shows next run time

**API Test:**
```bash
curl http://127.0.0.1:8000/schedule/status
```

---

#### 6. **Manual Refresh (New Emails Check)** ✅
**Test:**
- Use API to check for new emails
- Should only check recent emails (cost-efficient)

**API Test:**
```bash
curl -X POST http://127.0.0.1:8000/check-new-emails
```

**Expected Response:**
```json
{
  "has_new": true,
  "new_count": 2,
  "last_check": "2025-12-15T21:30:00",
  "message": "Found 2 new email(s) since last check."
}
```

---

#### 7. **Notification Status** ✅
**Test:**
- Check notification status

**API Test:**
```bash
curl http://127.0.0.1:8000/notification/status
```

**Expected Response:**
```json
{
  "last_check": "2025-12-15T21:30:00",
  "check_count": 5,
  "auto_schedule_time": "18:00",
  "next_auto_check": "Today at 18:00"
}
```

---

#### 8. **RAG Cache Statistics** ✅
**Test:**
- Check cache stats
- Ask same question twice (second should be instant)

**API Test:**
```bash
curl http://127.0.0.1:8000/cache/stats
```

**Expected Response:**
```json
{
  "total_entries": 15,
  "valid_entries": 15,
  "expired_entries": 0,
  "cache_file": "data/.rag_cache.json"
}
```

**Cache Test:**
1. Ask: "What events are happening this week?" (first time - slow)
2. Ask same question again (should be instant - cached)

---

#### 9. **Duplicate Prevention** ✅
**Test:**
- Run backfill script twice
- Second run should skip already processed files

**Test:**
```bash
python -m scripts.backfill_emails
```

**Expected:**
- First run: Uploads all files
- Second run: Shows "Skipped (already uploaded)" for existing files
- Only uploads new files

---

#### 10. **Health Check** ✅
**Test:**
```bash
curl http://127.0.0.1:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "store_configured": true,
  "next_email_ingestion": "2025-12-16 18:00:00"
}
```

---

## 🐛 Common Issues & Solutions

### Issue: "No files have been uploaded yet"
**Solution:**
```bash
python -m scripts.backfill_emails
```

### Issue: Rate limit errors (429)
**Solution:**
- Wait a few minutes
- Check cache stats (use cached responses)
- Reduce query frequency

### Issue: Calendar authentication fails
**Solution:**
- Delete `calendar_token.json`
- Restart server
- Re-authenticate when creating first event

### Issue: Voice input not working
**Solution:**
- Use Chrome or Edge (best support)
- Allow microphone permission
- Check browser console for errors

---

## 📊 Performance Testing

### Cache Performance
1. Ask a question (first time): ~10-20 seconds
2. Ask same question (cached): <1 second
3. **Cost savings**: 90% reduction for repeated questions

### Upload Performance
1. First upload: Processes all files
2. Second upload: Skips duplicates (much faster)
3. **Time savings**: 80-90% faster on subsequent runs

---

## 🎯 Test Scenarios

### Scenario 1: New User Flow
1. Start server
2. Open UI
3. Ask first question
4. Upload conversation image
5. Add event to calendar
6. Check schedule status

### Scenario 2: Daily Usage
1. Check for new emails (manual refresh)
2. Ask about upcoming events
3. Check cache stats
4. View schedule

### Scenario 3: Cost Optimization
1. Ask same question multiple times
2. Check cache stats
3. Run backfill twice (test duplicate prevention)
4. Verify only new data processed

---

## ✅ Testing Results Template

```
Date: ___________
Tester: ___________

Core Features:
[ ] RAG Chatbot - Working / Issues: ___________
[ ] Voice Input - Working / Issues: ___________
[ ] Image Upload - Working / Issues: ___________
[ ] Calendar Events - Working / Issues: ___________
[ ] Scheduled Ingestion - Working / Issues: ___________
[ ] Manual Refresh - Working / Issues: ___________
[ ] Cache System - Working / Issues: ___________

Performance:
[ ] Cache hit rate: _____%
[ ] Average response time (cached): _____ seconds
[ ] Average response time (uncached): _____ seconds
[ ] Upload time (first run): _____ seconds
[ ] Upload time (second run): _____ seconds

Issues Found:
1. ___________
2. ___________
3. ___________

Notes:
___________
```

---

## 🚀 Ready to Test!

All core features are implemented and ready for testing. Start with the UI at http://127.0.0.1:8000 and work through the checklist above.

Good luck! 🎉

