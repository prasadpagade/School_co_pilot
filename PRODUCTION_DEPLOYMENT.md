# 🚀 Production Deployment Guide

This guide covers deploying Denali School Copilot to production.

## Prerequisites

1. **Environment Variables**: Set up all required environment variables
2. **Google API Credentials**: Have `credentials.json` ready
3. **File Search Store**: Initialize the Gemini File Search Store
4. **Domain/Subdomain**: Have a domain ready (optional but recommended)

## Deployment Options

### Option 1: Render.com (Recommended for Quick Start)

1. **Create a Render Account**: Sign up at https://render.com

2. **Create New Web Service**:
   - Connect your GitHub repository
   - Select "Web Service"
   - Use these settings:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
     - **Environment**: Python 3.12

3. **Set Environment Variables** in Render dashboard:
   ```
   ENVIRONMENT=production
   GOOGLE_API_KEY=your_key_here
   FILE_SEARCH_STORE_NAME=your_store_name
   SCHOOL_DOMAINS=example.com
   SCHOOL_SENDERS=teacher@example.com
   EMAIL_INGESTION_TIME=18:00
   CORS_ORIGINS=https://your-app.onrender.com
   ```

4. **Deploy**: Render will automatically deploy on git push

5. **Update API URLs**: The app will auto-detect the production URL

### Option 2: Docker Deployment

1. **Build the Docker image**:
   ```bash
   docker build -t denali-school-copilot .
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Or run directly**:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e GOOGLE_API_KEY=your_key \
     -e FILE_SEARCH_STORE_NAME=your_store \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/credentials.json:/app/credentials.json:ro \
     denali-school-copilot
   ```

### Option 3: Railway.app

1. **Create Railway Account**: Sign up at https://railway.app

2. **New Project**: Create from GitHub repo

3. **Set Environment Variables**: Add all required env vars in Railway dashboard

4. **Deploy**: Railway auto-detects Python and deploys

### Option 4: Fly.io

1. **Install Fly CLI**: `curl -L https://fly.io/install.sh | sh`

2. **Login**: `fly auth login`

3. **Launch**: `fly launch` (follow prompts)

4. **Set Secrets**:
   ```bash
   fly secrets set GOOGLE_API_KEY=your_key
   fly secrets set FILE_SEARCH_STORE_NAME=your_store
   # ... etc
   ```

5. **Deploy**: `fly deploy`

## Environment Variables

Create a `.env` file or set these in your hosting platform:

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key
FILE_SEARCH_STORE_NAME=your_store_name

# Optional but recommended
SCHOOL_DOMAINS=example.com,another-school.com
SCHOOL_SENDERS=teacher@example.com
EMAIL_INGESTION_TIME=18:00
CORS_ORIGINS=https://your-domain.com
ENVIRONMENT=production

# Calendar (optional)
CALENDAR_ID=primary
DEFAULT_CALENDAR_ATTENDEES=partner@example.com
```

## Post-Deployment Checklist

- [ ] Verify health endpoint: `https://your-app.com/health`
- [ ] Test chat endpoint with a question
- [ ] Verify email ingestion is scheduled
- [ ] Check calendar integration (if enabled)
- [ ] Test mobile responsiveness
- [ ] Monitor logs for errors
- [ ] Set up error tracking (optional: Sentry)

## Performance Optimization

The app includes:
- ✅ GZip compression for responses
- ✅ Response caching for RAG queries
- ✅ Optimized file operations
- ✅ Mobile-responsive UI
- ✅ Production logging

## Monitoring

### Health Check Endpoint

```bash
curl https://your-app.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "store_configured": true,
  "next_email_ingestion": "2025-11-21T18:00:00"
}
```

### Logs

- **Render**: View logs in dashboard
- **Docker**: `docker logs <container_id>`
- **Railway**: View in dashboard
- **Fly.io**: `fly logs`

## Troubleshooting

### Common Issues

1. **"No files uploaded" error**:
   - Run email ingestion script locally first
   - Upload consolidated markdown files to Gemini

2. **CORS errors**:
   - Set `CORS_ORIGINS` to your actual domain
   - Don't use `*` in production

3. **Calendar not working**:
   - Ensure `credentials.json` is accessible
   - Check OAuth token is valid

4. **Rate limiting**:
   - Monitor API usage
   - Implement request throttling if needed

## Security Best Practices

1. **Never commit** `.env` or `credentials.json` to git
2. **Use environment variables** for all secrets
3. **Enable HTTPS** (most platforms do this automatically)
4. **Set proper CORS origins** (not `*` in production)
5. **Regular updates** of dependencies

## Scaling

For high traffic:
- Increase worker count: `--workers 4`
- Use a load balancer
- Consider Redis for distributed caching
- Database for metrics (instead of JSON files)

## Support

For issues, check:
- Application logs
- Health endpoint
- API status dashboard (if configured)

