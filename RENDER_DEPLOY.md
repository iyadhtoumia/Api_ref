# Deploy to Render - Step by Step

## Prerequisites

1. GitHub account with your code pushed to: https://github.com/iyadhtoumia/Api_ref
2. Get Macfax API key (free):
   ```powershell
   Invoke-RestMethod -Method Post -Uri 'https://macfax.com/api/v1/keys'
   ```
   Save the key, you'll need it!

## Deployment Steps

### 1. Go to Render
Visit: https://render.com

### 2. Sign Up/Login
- Click "Get Started for Free"
- Sign in with GitHub

### 3. Create New Web Service
- Click "New +" button (top right)
- Select "Web Service"

### 4. Connect Repository
- If first time: Click "Connect GitHub"
- Find: `iyadhtoumia/Api_ref`
- Click "Connect"

### 5. Configure Service

**Name:** `macfax-api` (or any name you want)

**Environment:** `Python 3`

**Region:** Choose closest to you (e.g., Oregon USA)

**Branch:** `main`

**Build Command:** (leave as auto-detected)
```
pip install -r requirements.txt
```

**Start Command:** (leave as auto-detected)
```
gunicorn app:app
```

**Plan:** `Free`

### 6. Add Environment Variable

Scroll down to "Environment Variables" section:

- Click "Add Environment Variable"
- **Key:** `MACFAX_API_KEY`
- **Value:** Paste your API key from step 1
- Click "Add"

### 7. Deploy!

- Click "Create Web Service" button at bottom
- Wait 2-3 minutes for deployment
- Watch the logs in real-time

### 8. Get Your URL

Once deployed, you'll see:
- **Status:** "Live" (green)
- **URL:** `https://macfax-api-xxxx.onrender.com`

Copy this URL!

### 9. Test Your API

Open in browser:
```
https://macfax-api-xxxx.onrender.com
```

You should see API documentation in JSON format.

Test an endpoint:
```
https://macfax-api-xxxx.onrender.com/api/lookup?serial=C02P73J9G8WP
```

### 10. Use Demo Page

1. Download `demo.html` from your repo
2. Open it in browser
3. Replace the API URL with your Render URL
4. Test all endpoints visually!

## Important Notes

### Free Tier Limitations
- **Sleep after 15 min inactivity** - First request after sleep takes ~30 seconds
- **750 hours/month** - About 30 days if used occasionally
- To prevent sleep: Upgrade to paid ($7/month) or use a ping service

### Keep Alive (Optional)
Add this to UptimeRobot or similar:
- URL: `https://your-app.onrender.com/health`
- Interval: Every 14 minutes

### Auto-Deploy
Any push to `main` branch will automatically redeploy!

### View Logs
In Render dashboard:
- Go to your service
- Click "Logs" tab
- See real-time requests and errors

### Update Environment Variables
1. Go to service dashboard
2. Click "Environment" in left menu
3. Edit variables
4. Service auto-restarts

## Troubleshooting

### Build Failed
- Check `requirements.txt` exists
- Verify Python syntax in `app.py`
- View build logs for errors

### Service Won't Start
- Check environment variable `MACFAX_API_KEY` is set
- View runtime logs
- Ensure port is not hardcoded (Render sets PORT automatically)

### API Returns Errors
- Test Macfax API directly: `curl https://macfax.com/api/v1/lookup?serial=C02P73J9G8WP`
- Check your API key is valid
- View logs for detailed errors

## Next Steps

1. ✅ Deploy to Render
2. ✅ Get your API URL
3. ✅ Test with demo.html
4. 📱 Integrate into your repair shop website
5. 💰 Start looking up devices and prices!

## Need Help?

- Render docs: https://render.com/docs
- Macfax docs: https://macfax.com/developers
- GitHub issues: https://github.com/iyadhtoumia/Api_ref/issues
