# ConvoGuide Deployment Guide

This guide covers how to deploy ConvoGuide to production and why CORS is not an issue with this architecture.

## Architecture Overview

```
┌─────────────────┐
│  Vercel         │  ← Frontend (Next.js) ✅ Deploy here
│  - UI           │
│  - /api/token   │
└────────┬────────┘
         │
         ├─── Connects to ───┐
         │                    │
┌────────┴────────┐   ┌──────┴──────────┐
│  LiveKit Cloud  │   │  Python Backend │  ← Agent Worker
│  - Manages rooms│   │  - STT/LLM/TTS  │     Deploy to Railway/Render/Fly
│  - Routes jobs  │   │  - Mode logic   │
└─────────────────┘   └─────────────────┘
```

## What Goes Where

### ✅ Frontend → Vercel

**Location**: `/frontend`

**What it does**:
- Next.js UI
- React components
- `/api/token` endpoint (generates LiveKit tokens)

**Deployment**:
```bash
cd frontend
vercel deploy --prod
```

### ❌ Python Agent → Cannot Use Vercel

**Location**: `/agent`

**Why not Vercel?**
- Needs to run as a **long-lived background process**
- Maintains **persistent WebSocket connection** to LiveKit Cloud
- Processes **real-time audio streams**
- Vercel only supports serverless functions (max 60s execution time)

**Deploy to**: Railway, Render, or Fly.io instead

---

## Deployment Options for Python Agent

### Option 1: Railway (Recommended - Easiest)

Perfect for Python workers, auto-deploys from GitHub.

**Setup**:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy from agent directory
cd agent
railway up
```

**Environment Variables** (set in Railway dashboard):
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxx
DEEPGRAM_API_KEY=xxxxxxx
CARTESIA_API_KEY=xxxxxxx
```

**Pros**:
- ✅ Dead simple deployment
- ✅ Free tier available ($5 credit/month)
- ✅ Auto-deploys on git push
- ✅ Built-in logs and metrics
- ✅ No configuration files needed

**Pricing**: ~$5-10/month after free tier

**Logs**:
```bash
railway logs
```

### Option 2: Render

Similar to Railway, generous free tier.

**Setup**:

Create `render.yaml` in project root:

```yaml
services:
  - type: worker
    name: convoguide-agent
    env: python
    region: oregon
    plan: free  # or starter ($7/month)
    buildCommand: "cd agent && pip install -r requirements.txt"
    startCommand: "cd agent && python -m src.main start"
    envVars:
      - key: LIVEKIT_URL
        sync: false
      - key: LIVEKIT_API_KEY
        sync: false
      - key: LIVEKIT_API_SECRET
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: DEEPGRAM_API_KEY
        sync: false
      - key: CARTESIA_API_KEY
        sync: false
```

**Deployment**:
```bash
# Connect GitHub repo in Render dashboard
# Render auto-deploys on push
```

**Pros**:
- ✅ Generous free tier (750 hours/month)
- ✅ Easy setup
- ✅ Good documentation
- ✅ Auto-deploy from GitHub

**Cons**:
- ⚠️ Free tier spins down after 15 min inactivity (60s cold start)

**Pricing**: Free tier, then $7/month starter

### Option 3: Fly.io

Best for low-latency, distributed deployments.

**Setup**:

Create `Dockerfile` in `/agent`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv and dependencies
RUN pip install uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Run agent
CMD ["uv", "run", "python", "-m", "src.main", "start"]
```

Create `fly.toml`:

```toml
app = "convoguide-agent"
primary_region = "sjc"  # San Jose - choose closest to your users

[build]

[env]
  # Public env vars (non-secret)

[processes]
  worker = "uv run python -m src.main start"
```

**Deployment**:
```bash
# Install flyctl
brew install flyctl  # macOS
# or: curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
cd agent
fly launch

# Set secrets
fly secrets set LIVEKIT_URL=wss://...
fly secrets set LIVEKIT_API_KEY=...
fly secrets set LIVEKIT_API_SECRET=...
fly secrets set OPENAI_API_KEY=...
fly secrets set DEEPGRAM_API_KEY=...
fly secrets set CARTESIA_API_KEY=...

# Deploy
fly deploy
```

**Pros**:
- ✅ Edge deployment (low latency globally)
- ✅ Free tier (3 shared-cpu VMs)
- ✅ Docker-based (very flexible)
- ✅ Great performance

**Cons**:
- ⚠️ Slightly more complex setup

**Pricing**: Free tier, then ~$3-5/month

### Option 4: Self-Hosted / Development

Run on your own machine or VPS.

**Local Development**:
```bash
cd agent
uv run python -m src.main dev
```

**Production on VPS** (Ubuntu/Debian):
```bash
# Install dependencies
sudo apt update
sudo apt install python3.11 python3-pip

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repo
git clone https://github.com/Lowellr/convoguide.git
cd convoguide/agent

# Install dependencies
uv sync

# Create systemd service
sudo nano /etc/systemd/system/convoguide.service
```

```ini
[Unit]
Description=ConvoGuide Agent
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/convoguide/agent
Environment="PATH=/home/youruser/.local/bin:/usr/bin"
ExecStart=/home/youruser/.local/bin/uv run python -m src.main start
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl enable convoguide
sudo systemctl start convoguide

# Check logs
sudo journalctl -u convoguide -f
```

---

## Complete Deployment Checklist

### Step 1: Deploy Frontend to Vercel

```bash
cd frontend

# Install Vercel CLI if needed
npm i -g vercel

# Deploy
vercel

# Follow prompts:
# - Link to existing project or create new
# - Select production
```

**Environment Variables** (set in Vercel dashboard):

Go to: Project Settings → Environment Variables

```env
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxx
```

**Vercel Dashboard**: https://vercel.com/dashboard

### Step 2: Deploy Python Agent to Railway

```bash
cd agent

# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

**Environment Variables** (set in Railway dashboard):

Go to: Project → Variables

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxx
DEEPGRAM_API_KEY=xxxxxxx
CARTESIA_API_KEY=xxxxxxx
```

**Railway Dashboard**: https://railway.app/dashboard

### Step 3: Verify Deployment

**Check Python Agent Logs**:

Railway:
```bash
railway logs
```

Render:
- Go to dashboard → Logs tab

Fly.io:
```bash
fly logs
```

**Look for**:
```
INFO livekit.agents starting worker
INFO livekit.agents registered worker
```

**Test Frontend**:

1. Visit your Vercel URL: `https://yourapp.vercel.app`
2. Enter your name
3. Click "Join Conversation"
4. Say "Tell me a joke"
5. Watch mode indicator change to 😄 Playful

---

## Why CORS is NOT an Issue

### Communication Flow

```
User Browser
    │
    │ 1. HTTP GET (same-origin ✅)
    ├──────────────────────────► /api/token (Vercel)
    │                             Returns: LiveKit token
    │
    │ 2. WebRTC connection (no CORS ✅)
    ├──────────────────────────► LiveKit Cloud
    │                             - Audio streams
    │                             - Data channels
    │                             - Mode updates
    │
    │                             LiveKit Cloud
    │                                  │
    │                                  │ 3. WebSocket (no CORS ✅)
    │                                  │
    │                             Railway Python Agent
    │                             - Processes audio
    │                             - Sends mode updates
    │                             - Never receives HTTP from browser
```

### Why No CORS Problems

1. **Frontend API Route** (`/api/token`)
   - Same domain as frontend → **No CORS**
   - Example: `yourapp.vercel.app` calling `yourapp.vercel.app/api/token`
   - This is a same-origin request

2. **LiveKit Connection**
   - Uses **WebRTC & WebSocket** → **Not subject to CORS**
   - CORS only applies to HTTP requests from browsers
   - WebRTC is peer-to-peer protocol (no HTTP)

3. **Python Agent on Railway**
   - **Initiates outbound connection** to LiveKit → **No CORS**
   - Acts as a client, not a server
   - Never receives HTTP requests from browsers
   - Browser doesn't know Railway exists

### Old Architecture (CORS Problems)

If you had CORS issues before, your architecture probably looked like this:

```
❌ OLD (CORS problems):

Browser ─────HTTP POST────► Railway Backend
         (cross-origin)     (different domain)
```

CORS error:
```
Access to fetch at 'https://myapp-production.up.railway.app'
from origin 'https://myapp.vercel.app' has been blocked by CORS policy
```

### New Architecture (No CORS)

```
✅ NEW (No CORS):

Browser ─────WebRTC─────► LiveKit Cloud ◄────WebSocket──── Railway Backend
     (not HTTP)                                 (outbound connection)
```

No CORS because:
- Browser never makes HTTP request to Railway
- All browser communication goes through LiveKit (WebRTC/WebSocket)
- Railway agent is a background worker, not a web server

---

## Environment Variables Reference

### Frontend (Vercel)

```env
# Required
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxx

# Optional (for analytics, etc.)
NEXT_PUBLIC_POSTHOG_KEY=phc_xxxxxxx
```

### Backend (Railway/Render/Fly)

```env
# Required - LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=secretxxxxxxxxx

# Required - AI Services
OPENAI_API_KEY=sk-xxxxxxx
DEEPGRAM_API_KEY=xxxxxxx
CARTESIA_API_KEY=xxxxxxx

# Optional - Logging
LOG_LEVEL=INFO
```

### Where to Get API Keys

| Service | Get API Key | Free Tier |
|---------|-------------|-----------|
| LiveKit | https://cloud.livekit.io | ✅ 50 GB/month |
| OpenAI | https://platform.openai.com/api-keys | ❌ Pay-as-you-go |
| Deepgram | https://console.deepgram.com | ✅ $200 credit |
| Cartesia | https://cartesia.ai | ✅ Free tier available |

---

## Cost Estimates

### Monthly Costs (Production)

| Service | Free Tier | Paid | Notes |
|---------|-----------|------|-------|
| **Frontend** |
| Vercel | ✅ Hobby (free) | $20/mo Pro | Hobby sufficient for most |
| **Backend** |
| Railway | ✅ $5 credit | $5-10/mo | Worker usage-based |
| Render | ✅ 750 hrs | $7/mo | Free tier has cold starts |
| Fly.io | ✅ 3 VMs free | $3-5/mo | Best performance/price |
| **Infrastructure** |
| LiveKit Cloud | ✅ 50 GB/mo | $0.04/GB | ~50 hours of calls/month free |
| **AI Services** |
| OpenAI (GPT-4o-mini) | ❌ | ~$0.001/request | Cheap! |
| Deepgram (STT) | ✅ $200 credit | $0.0043/min | ~46,500 mins free |
| Cartesia (TTS) | ✅ Free tier | $0.025/min | Check current pricing |

**Total for hobby use**: **$0-5/month**
**Total for production**: **$20-50/month**

### Usage Estimates

**Light usage** (personal project):
- 10 conversations/month
- 10 min/conversation
- Total: 100 minutes/month
- **Cost**: $0 (within free tiers)

**Medium usage** (startup MVP):
- 100 conversations/month
- 15 min/conversation
- Total: 1,500 minutes/month
- **Cost**: ~$20-30/month

**Heavy usage** (production app):
- 1,000 conversations/month
- 20 min/conversation
- Total: 20,000 minutes/month
- **Cost**: ~$100-200/month

---

## Troubleshooting Deployment

### Frontend Issues

**Problem**: "Failed to connect to room"

**Check**:
1. Environment variables are set in Vercel
2. `NEXT_PUBLIC_LIVEKIT_URL` starts with `wss://`
3. LiveKit API key/secret are correct
4. Browser console for errors

**Solution**:
```bash
# Verify .env.local matches Vercel env vars
cd frontend
cat .env.local

# Test token generation locally
curl http://localhost:3000/api/token?roomName=test&participantName=test
```

### Backend Issues

**Problem**: Agent not connecting to LiveKit

**Check Railway logs**:
```bash
railway logs
```

**Look for**:
```
✅ Good:
INFO livekit.agents registered worker

❌ Bad:
ERROR failed to connect to LiveKit
```

**Common issues**:
1. Wrong `LIVEKIT_URL` (must start with `wss://`)
2. Wrong API key/secret
3. Missing environment variables
4. Build failed (check Railway build logs)

**Solution**:
```bash
# Verify environment variables
railway variables

# Restart service
railway restart
```

### Audio Issues

**Problem**: Can hear agent but agent can't hear me

**Check**:
1. Browser microphone permissions
2. Browser console for WebRTC errors
3. LiveKit Cloud dashboard for connection status

**Solution**:
```javascript
// Check browser console for:
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => console.log('Mic access OK'))
  .catch(err => console.error('Mic access denied:', err))
```

### Mode Indicator Not Updating

**Check agent logs**:
```bash
railway logs | grep "Mode shifted"
```

**Should see**:
```
INFO convoguide Checking for mode in text: 'Tell me a joke'
INFO convoguide Detected mode: ConversationMode.HUMOR
INFO convoguide Mode shifted to: humor
INFO convoguide Sent mode update to frontend: humor
```

**Check browser console**:
```javascript
// Should see:
Raw mode update received: {"mode": "humor"}
Parsed mode data: {mode: 'humor'}
Setting mode to: humor
```

---

## Monitoring & Logs

### Railway

**View logs**:
```bash
railway logs
railway logs --tail 100
railway logs --filter "ERROR"
```

**Metrics**:
- Go to Railway dashboard → Metrics tab
- CPU, Memory, Network usage

### Render

**Logs**:
- Dashboard → Logs tab (web UI only)

**Metrics**:
- Dashboard → Metrics tab

### Fly.io

**View logs**:
```bash
fly logs
fly logs -a convoguide-agent
```

**Metrics**:
```bash
fly status
fly scale show
```

### LiveKit Cloud

**Dashboard**: https://cloud.livekit.io

**Monitor**:
- Active rooms
- Participant count
- Bandwidth usage
- Error rates

---

## Continuous Deployment

### Railway (Auto-deploy from GitHub)

**Setup**:
1. Go to Railway dashboard
2. Project → Settings → GitHub
3. Connect repository
4. Select branch (main)
5. ✅ Auto-deploys on every push to main

**Trigger manual deploy**:
```bash
railway up
```

### Render (Auto-deploy from GitHub)

**Setup**:
1. Connect GitHub repo in Render dashboard
2. Select branch
3. ✅ Auto-deploys on every push

**Manual deploy**:
- Dashboard → Manual Deploy → Deploy latest commit

### Vercel (Auto-deploy from GitHub)

**Setup**:
1. Import GitHub repo in Vercel dashboard
2. ✅ Auto-deploys on every push to main
3. Preview deployments for PRs

**Manual deploy**:
```bash
vercel --prod
```

---

## Rollback Strategy

### Railway

```bash
# View deployments
railway deployments

# Rollback to previous
railway rollback [deployment-id]
```

### Render

- Dashboard → Deploys tab → Revert to previous deployment

### Vercel

- Dashboard → Deployments → Promote to Production

---

## Security Best Practices

### 1. Never Commit Secrets

✅ Already protected by `.gitignore`:
```gitignore
.env
.env.local
.env.production.local
```

### 2. Rotate API Keys Regularly

**When to rotate**:
- Every 90 days
- After team member leaves
- If keys are exposed

**How to rotate**:
1. Generate new key in service dashboard
2. Update environment variable in hosting platform
3. Redeploy
4. Delete old key

### 3. Use Different Keys per Environment

```env
# Development (.env.local)
OPENAI_API_KEY=sk-dev-xxxxxxx

# Production (Railway/Vercel env vars)
OPENAI_API_KEY=sk-prod-xxxxxxx
```

### 4. LiveKit Room Security

Tokens are generated with:
- Room name
- Participant name
- Expiration time (default: 1 hour)

```typescript
// frontend/src/app/api/token/route.ts
const token = new AccessToken(apiKey, apiSecret, {
  identity: participantName,
  ttl: '1h',  // Token expires in 1 hour
});
```

---

## Next Steps

1. **Deploy frontend to Vercel**
   ```bash
   cd frontend && vercel
   ```

2. **Deploy agent to Railway**
   ```bash
   cd agent && railway up
   ```

3. **Set environment variables** in both platforms

4. **Test end-to-end**
   - Visit Vercel URL
   - Start conversation
   - Verify mode changes

5. **Monitor usage**
   - Check LiveKit dashboard
   - Watch Railway logs
   - Monitor API costs

---

## Support & Resources

- **LiveKit Docs**: https://docs.livekit.io
- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Project Repo**: https://github.com/Lowellr/convoguide
- **Architecture Doc**: See `ARCHITECTURE.md`

---

**Last Updated**: 2025-12-12
**Maintained By**: ConvoGuide Team
