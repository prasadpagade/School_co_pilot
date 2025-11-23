# 🚂 Deploy to Railway.app

## Quick Deploy (5 minutes)

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Production ready"
git push
```

### Step 2: Deploy on Railway

1. **Go to Railway**: https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. **Select your repository**: `school-copilot`
4. Railway will auto-detect Python

### Step 3: Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```
ENVIRONMENT=production
GOOGLE_API_KEY=your_gemini_api_key
FILE_SEARCH_STORE_NAME=your_store_name
SCHOOL_DOMAINS=example.com
SCHOOL_SENDERS=teacher@example.com
EMAIL_INGESTION_TIME=18:00
CORS_ORIGINS=https://your-app.up.railway.app
PYTHONUNBUFFERED=1
```

### Step 4: Configure Start Command

In Railway dashboard:
1. Go to **Settings** → **Deploy**
2. Set **Start Command**:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
   ```

### Step 5: Deploy

Railway will automatically:
- Install dependencies from `requirements.txt`
- Start the app
- Give you a URL like: `https://your-app.up.railway.app`

## Railway Advantages

✅ **Free tier**: $5 credit/month (usually enough for small apps)
✅ **Auto-deploys** on git push
✅ **Built-in HTTPS**
✅ **Easy environment variables**
✅ **Good for small to medium traffic**

## Custom Domain (Optional)

1. Go to **Settings** → **Domains**
2. Add your custom domain
3. Railway handles SSL automatically

## Monitoring

- View logs in Railway dashboard
- Check metrics in **Metrics** tab
- Set up alerts if needed

## Troubleshooting

**Build fails?**
- Check logs in Railway dashboard
- Verify `requirements.txt` is correct
- Check Python version (should be 3.12)

**App not starting?**
- Check start command is correct
- Verify all environment variables are set
- Check logs for errors

