# 📅 Calendar Testing Guide

## ✅ Calendar Features Implemented

1. **Calendar Event Creation** - Create events in Google Calendar
2. **Image to Calendar** - Upload conversation images, extract dates, create events
3. **Voice to Calendar** - Speak calendar commands, auto-create events
4. **Date Extraction** - Extract dates from text/images
5. **Calendar Sharing** - Add attendees automatically

---

## 🧪 Testing Calendar Features

### Test 1: Basic Calendar Event Creation

**Via UI:**
1. Go to Calendar tab
2. Upload a conversation image with dates
3. Click "Add to Calendar" for extracted events

**Via API:**
```bash
curl -X POST http://127.0.0.1:8000/create-calendar-event \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Music class",
    "date": "2025-12-15",
    "time": "15:00",
    "description": "Music class for Denali",
    "attendees": ["your-email@example.com"]
  }'
```

**Expected:**
- Event created in Google Calendar
- Attendees invited (if provided)
- Reminder set (60 minutes before)
- Returns event link

---

### Test 2: Voice Calendar Commands ⭐ NEW

**How to Test:**
1. Click microphone button
2. Say one of these commands:
   - "Add Music class on December 15th at 3pm"
   - "Create reminder for field trip tomorrow"
   - "Schedule parent teacher conference next week"
   - "Add to calendar: Book fair on November 20th"

**Expected:**
- System detects calendar intent
- Extracts date and event details
- Creates calendar event automatically
- Shows success message with link

**Via API:**
```bash
curl -X POST http://127.0.0.1:8000/voice-calendar \
  -H "Content-Type: application/json" \
  -d '{"text": "Add Music class on December 15th at 3pm"}'
```

---

### Test 3: Image Upload to Calendar

**Steps:**
1. Take screenshot of conversation with dates
2. Go to Calendar tab
3. Click "Choose Image"
4. Select image
5. Wait for processing

**Expected:**
- Extracts dates from image
- Shows extracted events
- Option to add each event to calendar
- Or auto-creates if configured

---

### Test 4: Date Extraction from Text

**Via API:**
```bash
curl -X POST http://127.0.0.1:8000/extract-dates \
  -H "Content-Type: application/json" \
  -d '{"text": "On 15th, 16th Dec Denali has Music class"}'
```

**Expected:**
```json
{
  "events": [
    {
      "title": "Music class",
      "date": "2025-12-15T00:00:00",
      "time": null,
      "description": "On 15th, 16th Dec Denali has Music class",
      "confidence": 0.95
    }
  ],
  "message": "Extracted 1 event(s) from text"
}
```

---

## 🔐 First-Time Calendar Setup

### Step 1: Enable Calendar API
1. Go to Google Cloud Console
2. Enable "Google Calendar API"
3. Same credentials.json file works (already has calendar scopes)

### Step 2: Authenticate
1. Create your first calendar event (via UI or API)
2. Browser will open for OAuth
3. Authorize calendar access
4. Token saved to `calendar_token.json`

### Step 3: Configure Attendees (Optional)
Add to `.env`:
```bash
DEFAULT_CALENDAR_ATTENDEES=wife@example.com,partner@example.com
```

---

## 🎤 Voice Calendar Commands - Examples

### Supported Formats:
- "Add [event] on [date] at [time]"
- "Create reminder for [event] [date]"
- "Schedule [event] [date]"
- "Add to calendar: [event] on [date]"

### Examples:
1. **"Add Music class on December 15th at 3pm"**
   - Extracts: Music class, Dec 15, 3:00 PM
   - Creates event

2. **"Create reminder for field trip tomorrow"**
   - Extracts: Field trip, tomorrow's date
   - Creates event

3. **"Schedule parent teacher conference next week"**
   - Extracts: Parent teacher conference, next week's date
   - Creates event

4. **"Add to calendar: Book fair on November 20th"**
   - Extracts: Book fair, Nov 20
   - Creates event (defaults to 9am)

---

## ✅ Verification Checklist

### Calendar Integration:
- [ ] Calendar API enabled in Google Cloud Console
- [ ] `calendar_token.json` created (after first auth)
- [ ] Can create events via API
- [ ] Can create events via UI
- [ ] Events appear in Google Calendar
- [ ] Attendees receive invitations (if configured)
- [ ] Reminders set correctly (60 min before)

### Voice Calendar:
- [ ] Voice input detects calendar keywords
- [ ] Extracts dates from voice commands
- [ ] Creates events automatically
- [ ] Shows success message
- [ ] Provides calendar link

### Image to Calendar:
- [ ] Upload image works
- [ ] Extracts dates from images
- [ ] Shows extracted events
- [ ] Can add events to calendar
- [ ] Events created correctly

---

## 🐛 Troubleshooting

### Issue: "Calendar authentication failed"
**Solution:**
1. Delete `calendar_token.json`
2. Try creating an event again
3. Re-authorize in browser

### Issue: "No dates extracted"
**Solution:**
- Be more specific: "Add Music class on December 15th at 3pm"
- Include date and time
- Try different formats

### Issue: "Events not appearing in calendar"
**Solution:**
- Check `CALENDAR_ID` in `.env` (should be "primary")
- Verify calendar authentication
- Check Google Calendar app/website

### Issue: "Voice not detecting calendar commands"
**Solution:**
- Use clear calendar keywords: "add to calendar", "create event", "schedule"
- Speak clearly
- Check browser console for errors

---

## 📊 Test Results Template

```
Date: ___________
Calendar Test Results:

Basic Event Creation:
[ ] API endpoint works
[ ] UI button works
[ ] Event appears in Google Calendar
[ ] Attendees invited (if configured)
[ ] Reminders set

Voice Calendar:
[ ] Voice detection works
[ ] Date extraction works
[ ] Event creation works
[ ] Success message shown
[ ] Calendar link provided

Image to Calendar:
[ ] Image upload works
[ ] Date extraction works
[ ] Events displayed
[ ] Can add to calendar

Issues Found:
1. ___________
2. ___________

Notes:
___________
```

---

## 🚀 Ready to Test!

Start the server and test:
1. **Voice Calendar**: Click mic, say "Add Music class on December 15th at 3pm"
2. **Image Upload**: Upload a conversation screenshot
3. **API Test**: Use curl commands above

Good luck! 🎉

