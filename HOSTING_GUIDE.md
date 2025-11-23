# Hosting & Beta Testing Guide

## 🚀 Hosting Options

### Option 1: Railway (Recommended for Quick Setup)
**Best for:** Fast deployment, automatic HTTPS, easy scaling

1. **Sign up**: https://railway.app
2. **Create new project** → "Deploy from GitHub repo"
3. **Add environment variables** in Railway dashboard:
   - `GOOGLE_API_KEY`
   - `FILE_SEARCH_STORE_NAME`
   - `GMAIL_CLIENT_ID`
   - `GMAIL_CLIENT_SECRET`
   - `GMAIL_REDIRECT_URI` (use Railway's domain)
   - `CALENDAR_ID` (optional, defaults to "primary")
   - `DEFAULT_CALENDAR_ATTENDEES` (comma-separated emails)
   - `EMAIL_INGESTION_TIME` (default: "18:00")
   - `SCHOOL_DOMAINS` (comma-separated)
   - `SCHOOL_SENDERS` (comma-separated)

4. **Add `Procfile`**:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

5. **Upload credentials**: Use Railway's file storage or environment variables

**Cost**: ~$5-20/month depending on usage

### Option 2: Render
**Best for:** Free tier available, easy setup

1. **Sign up**: https://render.com
2. **Create Web Service** → Connect GitHub repo
3. **Build command**: `pip install -r requirements.txt`
4. **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Add environment variables** (same as Railway)

**Cost**: Free tier available, $7/month for always-on

### Option 3: Google Cloud Run
**Best for:** Serverless, pay-per-use, integrates with Google APIs

1. **Install gcloud CLI**
2. **Build container**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/school-copilot
   ```
3. **Deploy**:
   ```bash
   gcloud run deploy school-copilot \
     --image gcr.io/PROJECT_ID/school-copilot \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```
4. **Set environment variables** in Cloud Run console

**Cost**: Pay-per-use, typically $5-15/month

### Option 4: DigitalOcean App Platform
**Best for:** Simple pricing, good performance

1. **Sign up**: https://www.digitalocean.com
2. **Create App** → Connect GitHub
3. **Configure build/run commands**
4. **Add environment variables**

**Cost**: $5-12/month

## 🔐 Security Best Practices

### 1. Environment Variables
- **Never commit** `.env`, `credentials.json`, or `token.json` to Git
- Use hosting platform's secret management
- Rotate credentials regularly

### 2. OAuth Redirect URIs
- Update `GMAIL_REDIRECT_URI` in Google Cloud Console to match your hosted domain
- Add both `http://localhost` (for local dev) and your production URL

### 3. API Keys
- Restrict API keys in Google Cloud Console
- Set up billing alerts
- Monitor usage regularly

### 4. Access Control
- Consider adding authentication (e.g., Auth0, Firebase Auth)
- Use HTTPS only in production
- Implement rate limiting

## 👥 Beta Testing Setup

### 1. Share Access
- **Option A**: Share the hosted URL with family members
- **Option B**: Set up user accounts (requires auth implementation)

### 2. Calendar Sharing
- In Google Calendar, share your calendar with family members
- Set permissions: "See all event details" or "Make changes to events"
- Or use `DEFAULT_CALENDAR_ATTENDEES` in config to auto-invite

### 3. Email Filters
- Configure `SCHOOL_DOMAINS` and `SCHOOL_SENDERS` in `.env`
- Test with a few emails first
- Adjust filters based on what emails are being captured

### 4. Testing Checklist
- [ ] Email ingestion works
- [ ] Calendar events are created correctly
- [ ] Image upload extracts dates properly
- [ ] Voice input works
- [ ] Scheduled ingestion runs at correct time
- [ ] Chat responses are accurate
- [ ] Calendar sharing works with family

### 5. Feedback Collection
- Create a simple feedback form or use Google Forms
- Monitor error logs
- Track common questions/issues

## 📊 Monitoring

### 1. Application Health
- Check `/health` endpoint regularly
- Monitor `/schedule/status` for ingestion schedule

### 2. API Usage
- Monitor Google API usage: https://console.cloud.google.com/apis/dashboard
- Set up billing alerts
- Track Gemini API costs: https://ai.dev/usage

### 3. Error Tracking
- Use services like Sentry (free tier available)
- Or log errors to a file and review regularly

## 🔄 Updates & Maintenance

### 1. Code Updates
- Use Git for version control
- Deploy updates through your hosting platform
- Test locally before deploying

### 2. Data Backup
- Backup `data/raw_emails/` and `data/attachments/` regularly
- Consider automated backups

### 3. Dependency Updates
- Regularly update `requirements.txt`
- Test updates in development first

## 💰 Cost Estimates

### Monthly Costs (Approximate)
- **Hosting**: $5-20/month (depending on platform)
- **Gemini API**: $5-15/month (with $20 budget cap)
- **Gmail API**: Free
- **Calendar API**: Free
- **Total**: ~$10-35/month

### Cost Optimization
- Use free tiers when possible
- Set API budget limits
- Monitor usage and optimize queries
- Consider caching responses

## 🐛 Troubleshooting

### Common Issues

1. **OAuth Errors**
   - Check redirect URI matches exactly
   - Verify credentials are correct
   - Clear tokens and re-authenticate

2. **Scheduled Tasks Not Running**
   - Check server timezone
   - Verify scheduler is initialized
   - Check logs for errors

3. **Calendar Events Not Created**
   - Verify calendar permissions
   - Check authentication token
   - Verify attendee emails are valid

4. **Image Processing Fails**
   - Check file size limits
   - Verify image format is supported
   - Check Gemini API quota

## 📝 Production Checklist

- [ ] All environment variables set
- [ ] OAuth redirect URIs updated
- [ ] HTTPS enabled
- [ ] Error logging configured
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] API budget limits set
- [ ] Calendar sharing configured
- [ ] Beta testers added
- [ ] Documentation shared with users

