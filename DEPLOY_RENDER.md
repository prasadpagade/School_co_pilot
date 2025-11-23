# 🎨 Deploy to Render.com

## Quick Deploy (5 minutes)

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Production ready"
git push
```

### Step 2: Deploy on Render

1. **Go to Render**: https://render.com
2. **New +** → **Web Service**
3. **Connect GitHub** → Select your repository
4. **Configure Service**:
   - **Name**: `denali-school-copilot` (or your choice)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: `.` (leave as is)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`

### Step 3: Add Environment Variables

In Render dashboard, go to **Environment** section and add:

```
ENVIRONMENT=production
GOOGLE_API_KEY=your_gemini_api_key
FILE_SEARCH_STORE_NAME=your_store_name
SCHOOL_DOMAINS=example.com
SCHOOL_SENDERS=teacher@example.com
EMAIL_INGESTION_TIME=18:00
CORS_ORIGINS=https://your-app.onrender.com
PYTHONUNBUFFERED=1
```

### Step 4: Deploy

Click **Create Web Service**

Render will:
- Build your app
- Deploy it
- Give you a URL like: `https://denali-school-copilot.onrender.com`

## Render Advantages

✅ **Free tier**: 750 hours/month (enough for always-on)
✅ **Auto-deploys** on git push
✅ **Built-in HTTPS**
✅ **Easy to use dashboard**
✅ **Good documentation**

## Custom Domain (Optional)

1. Go to **Settings** → **Custom Domains**
2. Add your domain
3. Render handles SSL automatically

## Auto-Deploy Settings

Render auto-deploys on every push to your main branch. To disable:
- Go to **Settings** → **Auto-Deploy**
- Toggle off if needed

## Monitoring

- View logs in **Logs** tab
- Check metrics in **Metrics** tab
- Set up alerts in **Alerts** section

## Troubleshooting

**Build fails?**
- Check **Logs** tab for errors
- Verify `requirements.txt` is correct
- Check Python version (should be 3.12)

**App crashes?**
- Check **Logs** for error messages
- Verify all environment variables are set
- Check `/health` endpoint

**Sleep mode (Free tier)?**
- Free tier apps sleep after 15 min of inactivity
- First request after sleep takes ~30 seconds
- Upgrade to paid plan for always-on

