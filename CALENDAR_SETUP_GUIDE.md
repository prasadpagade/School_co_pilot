# 📅 Google Calendar Setup Guide

## For Developers (You)

### Step 1: Enable Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one)
3. Go to **APIs & Services** > **Library**
4. Search for "Google Calendar API"
5. Click **Enable**

### Step 2: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (unless you have a Google Workspace)
3. Fill in required fields:
   - App name: "Denali School Copilot"
   - User support email: Your email
   - Developer contact: Your email
4. Add scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
5. Add test users (your email) if app is in testing mode
6. Save

### Step 3: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Desktop app**
4. Name it: "Denali School Copilot Desktop"
5. Download the JSON file
6. Save as `credentials.json` in project root

### Step 4: Test Calendar Integration

1. Start server: `uvicorn app.main:app --reload`
2. Try creating a calendar event via chat
3. Browser will open for OAuth authorization
4. Authorize access
5. Token saved to `calendar_token.json`

✅ **Done!** Calendar integration is now working.

---

## For Customers (Simplified Experience)

### Option 1: Pre-configured OAuth (Recommended)

**Best for:** SaaS model where you manage the OAuth app

1. **You (developer) set up OAuth once** in Google Cloud Console
2. **Customers just authorize** - no API setup needed
3. **One-click authorization** when they first use calendar features

**Implementation:**
- Use your OAuth client ID/secret
- Customers authorize through your app
- They never see Google Cloud Console

### Option 2: Self-Service Setup (Current)

**Best for:** Self-hosted or enterprise customers

1. Provide a **setup wizard** in the UI
2. Guide them through:
   - Creating Google Cloud project
   - Enabling Calendar API
   - Downloading credentials
   - Uploading credentials file
3. **Automated checks** to verify setup

### Option 3: Service Account (Enterprise)

**Best for:** Organizations with Google Workspace

1. Create service account in Google Cloud
2. Share calendar with service account
3. No user authorization needed
4. Works for all users automatically

---

## Recommended Customer Experience

### Setup Wizard Flow

1. **First-time calendar use:**
   ```
   User clicks "Add to Calendar"
   → "Calendar not set up yet"
   → "Let's set it up!" button
   → Setup wizard opens
   ```

2. **Setup wizard steps:**
   - Step 1: "We'll help you connect Google Calendar"
   - Step 2: "Click here to create Google Cloud project" (opens guide)
   - Step 3: "Upload your credentials.json file"
   - Step 4: "Test connection" (creates test event)
   - Step 5: "✅ All set! Calendar is connected"

3. **Status indicator:**
   - Show calendar connection status in UI
   - "Calendar: ✅ Connected" or "Calendar: ⚠️ Not set up"

### Alternative: Embedded Setup

For paying customers, you could:
1. **Pre-configure OAuth** for all customers
2. **One-click authorization** - they just click "Connect Calendar"
3. **No technical setup** required

---

## Error Handling Improvements

Current errors should show:
- "Calendar API not enabled" → Link to enable guide
- "OAuth not configured" → Link to setup wizard
- "Authorization failed" → Retry button with clear instructions

---

## Next Steps

1. ✅ Add setup wizard to UI
2. ✅ Add calendar status indicator
3. ✅ Improve error messages with actionable steps
4. ✅ Consider pre-configured OAuth for SaaS customers

