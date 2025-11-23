# 🚀 Quick Start: Production Deployment

## Fastest Way to Deploy (Render.com - 5 minutes)

1. **Push to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Production ready"
   git push
   ```

2. **Go to Render.com**:
   - Sign up/login at https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repo

3. **Configure Service**:
   - **Name**: `denali-school-copilot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`

4. **Add Environment Variables** (in Render dashboard):
   ```
   ENVIRONMENT=production
   GOOGLE_API_KEY=your_key
   FILE_SEARCH_STORE_NAME=your_store
   SCHOOL_DOMAINS=example.com
   SCHOOL_SENDERS=teacher@example.com
   EMAIL_INGESTION_TIME=18:00
   CORS_ORIGINS=https://your-app.onrender.com
   ```

5. **Deploy**: Click "Create Web Service"

6. **Test**: Visit your app URL and test the chat!

## Pre-Deployment Checklist

Before deploying, ensure:

- [ ] Email ingestion has been run at least once
- [ ] Consolidated markdown files exist in `data/consolidated/`
- [ ] Files have been uploaded to Gemini (run upload script)
- [ ] All environment variables are set
- [ ] `credentials.json` is accessible (if using calendar)

## Testing Production Locally

Test production mode locally:

```bash
export ENVIRONMENT=production
export GOOGLE_API_KEY=your_key
export FILE_SEARCH_STORE_NAME=your_store
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## Mobile Testing

1. Open your app on a mobile device
2. Test:
   - Chat interface responsiveness
   - Voice input
   - Image upload
   - Calendar features
   - Tab navigation

## Performance Tips

- **Caching**: Responses are cached for 7 days
- **Compression**: GZip enabled automatically
- **Workers**: Adjust based on traffic (2-4 recommended)
- **Monitoring**: Check `/health` endpoint regularly

## Troubleshooting

**App not loading?**
- Check health endpoint: `https://your-app.com/health`
- Verify environment variables
- Check logs in hosting dashboard

**RAG not working?**
- Ensure files are uploaded to Gemini
- Check `FILE_SEARCH_STORE_NAME` is correct
- Run email ingestion if needed

**Mobile UI issues?**
- Clear browser cache
- Check viewport meta tag is present
- Test on different devices

## Next Steps

1. Set up custom domain (optional)
2. Configure email notifications
3. Monitor performance metrics
4. Set up error tracking (Sentry, etc.)

For detailed deployment options, see `PRODUCTION_DEPLOYMENT.md`

