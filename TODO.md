# 📋 To-Do List for Tomorrow

## ✅ Completed Today
- [x] Calendar integration with Google Calendar API
- [x] Voice-to-calendar commands
- [x] Date extraction from images and text
- [x] Email notification system
- [x] Manual email check button
- [x] Miss Lobeda email highlighting
- [x] Recent emails display
- [x] UI/UX improvements
- [x] Automatic calendar event listing
- [x] Improved time extraction

---

## 🎯 Priority 1: High-Value Features (Next Session)

### 1. Weekly Summary Email ⭐ HIGH PRIORITY
**Time Estimate:** 2-3 days
- [ ] Create `app/weekly_summary.py`
- [ ] Generate summary every Sunday at 6PM
- [ ] Extract from all emails received that week
- [ ] Summarize: events, forms, payments, items needed
- [ ] Format as HTML email
- [ ] Create `app/email_sender.py` for SMTP/SendGrid
- [ ] Create `templates/weekly_summary.html`
- [ ] Add "View in App" button
- [ ] Test email delivery

**Value:** $10-20/month feature, high customer retention

---

### 2. Daily "Tomorrow Prep" Message ⭐ HIGH PRIORITY
**Time Estimate:** 2-3 days
- [ ] Create `app/daily_prep.py`
- [ ] Schedule for 7PM daily
- [ ] Extract tomorrow's schedule (PE, library, specials)
- [ ] Extract items needed (library book, jacket, snack)
- [ ] Extract dismissal time changes
- [ ] Format concise message
- [ ] Send via push notification or email
- [ ] Test with real data

**Value:** Daily habit builder, high engagement

---

### 3. Manual Refresh UI Button
**Time Estimate:** 1 day
- [x] Backend API ready (`/check-new-emails`)
- [ ] Add "Check for New Emails" button in Schedule tab (DONE)
- [ ] Add notification badge when new emails found
- [ ] Show count of new emails
- [ ] Add "Refresh Now" button in Chat tab (optional)

**Status:** Mostly done, just needs polish

---

### 4. Action Board Dashboard ⭐ MVP FEATURE
**Time Estimate:** 5-7 days
- [ ] Create `app/action_board.py`
- [ ] Create `app/action_extractor.py`
- [ ] Extract actionable items from emails:
  - Forms to fill
  - Payments due
  - Items needed
  - Events to RSVP
- [ ] Create dashboard UI component
- [ ] Add "Mark as Done" functionality
- [ ] Track completion status
- [ ] Add new tab: "Action Board"
- [ ] Categorize actions (Forms, Payments, Items, Events)

**Value:** Core MVP feature, high user value

---

## 🔧 Priority 2: Bug Fixes & Improvements

### 5. Image Time Extraction Fix
**Time Estimate:** 2-3 hours
- [ ] Test image upload with time formats
- [ ] Improve OCR time parsing (4:00 p.m., 4pm, etc.)
- [ ] Verify time extraction from conversation images
- [ ] Test with various time formats

**Status:** Partially working, needs testing

---

### 6. Calendar Event Parsing Improvements
**Time Estimate:** 2-3 hours
- [ ] Test calendar command parsing
- [ ] Improve date/time extraction accuracy
- [ ] Handle edge cases (relative dates, time zones)
- [ ] Better error messages for failed parsing

---

### 7. Email Ingestion Testing
**Time Estimate:** 1-2 hours
- [ ] Verify email ingestion is working
- [ ] Check duplicate prevention
- [ ] Test scheduled ingestion (6pm)
- [ ] Verify new emails are being detected

---

## 🚀 Priority 3: Enhanced Features

### 8. Enhanced Calendar Sync
**Time Estimate:** 3-4 days
- [ ] Auto-detect event types (field trip, picture day, half day)
- [ ] Set appropriate calendar colors
- [ ] Add location automatically
- [ ] Set smart reminders based on event type
- [ ] Sync with Apple Calendar (iCal export)

---

### 9. Multi-Child Support
**Time Estimate:** 5-7 days
- [ ] Add `children` table/model
- [ ] Update email filters to support multiple children
- [ ] Add child selector in UI
- [ ] Update RAG to filter by child
- [ ] Update calendar to show child name in events
- [ ] Create `app/children.py`

---

### 10. Allergy & Dietary Alerts
**Time Estimate:** 3-4 days
- [ ] Add allergy settings to user profile
- [ ] Create `app/allergy_checker.py`
- [ ] Scan email content for food mentions
- [ ] Generate alerts
- [ ] Show in Action Board

---

## 🎨 Priority 4: UI/UX Polish

### 11. UI Improvements
**Time Estimate:** 2-3 days
- [ ] Improve mobile responsiveness
- [ ] Add loading states
- [ ] Better error messages
- [ ] Add tooltips and help text
- [ ] Improve color scheme consistency
- [ ] Add animations/transitions

---

### 12. Notification System Enhancements
**Time Estimate:** 1-2 days
- [ ] Add browser notifications (if user allows)
- [ ] Sound alerts for Miss Lobeda emails
- [ ] Email notification preferences
- [ ] Notification history

---

## 📊 Priority 5: Testing & Quality

### 13. Comprehensive Testing
**Time Estimate:** 2-3 days
- [ ] Test all calendar features
- [ ] Test email ingestion flow
- [ ] Test notification system
- [ ] Test voice commands
- [ ] Test image upload
- [ ] Load testing
- [ ] Error handling testing

---

### 14. Documentation
**Time Estimate:** 1-2 days
- [ ] Update README with new features
- [ ] Create user guide
- [ ] Document API endpoints
- [ ] Create setup video/walkthrough

---

## 💰 Priority 6: Monetization Prep

### 15. Beta Testing Setup
**Time Estimate:** 3-4 days
- [ ] Set up hosting (see HOSTING_GUIDE.md)
- [ ] Create beta tester onboarding flow
- [ ] Add user accounts/authentication
- [ ] Set up feedback collection
- [ ] Create beta tester dashboard

---

### 16. Payment Integration (Future)
**Time Estimate:** 5-7 days
- [ ] Choose payment processor (Stripe/Paddle)
- [ ] Add subscription tiers
- [ ] Create pricing page
- [ ] Add payment processing
- [ ] Handle subscription management

---

## 🐛 Known Issues to Fix

### Issue 1: Image Time Extraction
- **Status:** Partially working
- **Fix:** Improve time parsing in `app/date_extractor.py`
- **Priority:** Medium

### Issue 2: Email Sorting
- **Status:** Fixed (now sorts by date)
- **Verify:** Test that newest emails show first

### Issue 3: Miss Lobeda Email Visibility
- **Status:** Fixed (no auto-hide)
- **Verify:** Test that notifications stay visible

---

## 📝 Quick Wins (1-2 hours each)

- [ ] Add keyboard shortcuts (e.g., Cmd+K for chat)
- [ ] Add "Clear Chat" button
- [ ] Add export calendar events (iCal)
- [ ] Add email search/filter
- [ ] Add dark mode toggle
- [ ] Add print-friendly view

---

## 🎯 Recommended Focus for Tomorrow

**Start with:**
1. **Weekly Summary Email** (highest value, 2-3 days)
2. **Daily Prep Message** (high engagement, 2-3 days)
3. **Action Board** (MVP feature, 5-7 days)

**Quick fixes:**
- Test and fix image time extraction
- Polish notification UI
- Test email sorting

---

## 📊 Progress Tracking

**Completed Today:** 10 features
**Remaining High Priority:** 4 features
**Total Features:** 30+ features planned

**Next Milestone:** Weekly Summary + Daily Prep = $20-30/month value proposition

---

## 💡 Notes for Tomorrow

- Test calendar features thoroughly
- Verify email notifications work correctly
- Check that Miss Lobeda emails stay visible
- Verify recent emails show newest first
- Consider adding browser notifications for real-time alerts
- Think about adding a "Mark as Read" for notifications

---

**Good work today! 🎉**

