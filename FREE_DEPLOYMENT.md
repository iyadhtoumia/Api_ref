# Free Deployment Options

## 1. Render.com (Easiest - Recommended)

### Steps:
1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Render auto-detects Python
6. Add environment variable: `MACFAX_API_KEY`
7. Deploy!

**Free Tier:**
- 750 hours/month
- Sleeps after 15 min inactivity
- Auto-wakes on request

**Config:** Already created `render.yaml`

---

## 2. Railway.app

### Steps:
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select your repo
5. Add environment variable: `MACFAX_API_KEY`
6. Deploy!

**Free Tier:**
- $5 credit/month
- ~100 hours of usage

**Config:** Already created `railway.toml`

---

## 3. Fly.io

### Steps:
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch

# Set secret
fly secrets set MACFAX_API_KEY=your_key_here

# Deploy
fly deploy
```

**Free Tier:**
- 3 shared VMs
- 160GB bandwidth/month

**Config:** Already created `fly.toml`

---

## 4. PythonAnywhere (For Scripts)

### Steps:
1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Go to "Files" → Upload your files
3. Go to "Bash" console:
```bash
pip install -r requirements.txt --user
```
4. Create scheduled task or run manually

**Free Tier:**
- One web app
- Limited CPU
- Good for research scripts

**Usage:**
```bash
python macfax_research.py lookup C02P73J9G8WP
```

---

## 5. Google Cloud Run

### Steps:
```bash
# Install gcloud CLI
# Build and deploy
gcloud run deploy macfax-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MACFAX_API_KEY=your_key

```

**Free Tier:**
- 2 million requests/month
- 360,000 GB-seconds compute
- Only charged when running

---

## 6. Vercel (Serverless)

Create `api/index.py`:
```python
from macfax_client import MacfaxClient

def handler(request):
    client = MacfaxClient()
    serial = request.args.get('serial')
    result = client.lookup_serial(serial)
    return result
```

### Steps:
```bash
npm i -g vercel
vercel
```

**Free Tier:**
- 100GB bandwidth
- Serverless functions
- Instant deployment

---

## Comparison

| Platform | Free Tier | Best For | Setup Time |
|----------|-----------|----------|------------|
| **Render** | 750hrs/mo | Web apps | 5 min ⭐ |
| **Railway** | $5/mo credit | APIs | 3 min |
| **Fly.io** | 3 VMs | Global apps | 10 min |
| **PythonAnywhere** | 1 app | Scripts | 5 min |
| **Cloud Run** | 2M req/mo | Scalable APIs | 15 min |
| **Vercel** | 100GB | Serverless | 5 min |

---

## Quick Start: Render (Recommended)

1. Create GitHub repo:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/macfax-api.git
git push -u origin main
```

2. Deploy on Render:
- Visit render.com
- New Web Service
- Connect repo
- Add `MACFAX_API_KEY` env var
- Deploy!

Your API will be live at: `https://macfax-api-xxxx.onrender.com`

---

## Environment Variables

All platforms need:
```
MACFAX_API_KEY=your_key_here
```

Get a free API key:
```bash
curl -X POST https://macfax.com/api/v1/keys
```

Or with PowerShell:
```powershell
Invoke-RestMethod -Method Post -Uri 'https://macfax.com/api/v1/keys'
```
