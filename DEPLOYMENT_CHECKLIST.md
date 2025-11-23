# 🚀 Production Deployment Checklist

## Pre-Deployment Steps

### 1. Environment Variables
Make sure you have these set in your hosting platform:

- [ ] `GOOGLE_API_KEY` - Your Gemini API key
- [ ] `FILE_SEARCH_STORE_NAME` - Your File Search Store name
- [ ] `SCHOOL_DOMAINS` - Email domains to filter (e.g., `example.com`)
- [ ] `SCHOOL_SENDERS` - Specific sender emails (optional)
- [ ] `EMAIL_INGESTION_TIME` - Default: `18:00`
- [ ] `ENVIRONMENT=production`
- [ ] `CORS_ORIGINS` - Your production domain (e.g., `https://your-app.onrender.com`)

### 2. Data Preparation
- [ ] Run email ingestion at least once locally
- [ ] Verify consolidated markdown files exist in `data/consolidated/`
- [ ] Upload files to Gemini (run upload script)
- [ ] Test RAG queries work locally

### 3. Credentials
- [ ] `credentials.json` is accessible (for calendar features)
- [ ] OAuth tokens are set up (if using calendar)

## Quick Deploy Options

### Option 1: Render.com (Easiest - Recommended)
1. Push code to GitHub
2. Go to https://render.com
3. New → Web Service
4. Connect GitHub repo
5. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
6. Add environment variables
7. Deploy!

**Free tier**: 750 hours/month (enough for always-on)

### Option 2: Railway.app
1. Sign up at https://railway.app
2. New Project → Deploy from GitHub
3. Add environment variables
4. Deploy!

### Option 3: Fly.io
1. Install Fly CLI
2. `fly launch`
3. `fly secrets set GOOGLE_API_KEY=...` (for each env var)
4. `fly deploy`

## Post-Deployment

- [ ] Test health endpoint: `https://your-app.com/health`
- [ ] Test chat functionality
- [ ] Test on mobile device
- [ ] Share URL with family members
- [ ] Set up email ingestion schedule (runs automatically)

## Sharing with Family

Once deployed, share:
- **App URL**: `https://your-app.onrender.com` (or your domain)
- **Instructions**: See `USER_GUIDE.md`

No installation needed - just open in browser!

## Monitoring

- Check `/health` endpoint regularly
- Monitor logs in hosting dashboard
- Check RAG metrics in the Metrics tab

