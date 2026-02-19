---
description: Deploy ScholarMind to Vercel (frontend) and HuggingFace Spaces (backend) with Neon PostgreSQL and cloud Redis
---

# Deploy ScholarMind to Production

## Prerequisites
- [Neon](https://neon.tech) account → Free PostgreSQL database
- [Upstash](https://upstash.com) or similar → Free Redis instance
- [HuggingFace](https://huggingface.co) account → Free Spaces (Docker)
- [Vercel](https://vercel.com) account → Free frontend hosting
- GitHub repo with the `backend/` and `frontend/` folders pushed

---

## Step 1: Set Up Neon PostgreSQL

1. Go to [https://console.neon.tech](https://console.neon.tech)
2. Create a new project → name it `scholarmind`
3. Copy the connection string (looks like):
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/scholarmind?sslmode=require
   ```
4. Save this as `DATABASE_URL` — you'll use it in both HF Spaces and local testing

---

## Step 2: Set Up Cloud Redis (Upstash)

1. Go to [https://console.upstash.com](https://console.upstash.com)
2. Create a new Redis database → name it `scholarmind-cache`
3. Copy the Redis URL (looks like):
   ```
   redis://default:xxxxxx@us1-xxx.upstash.io:6379
   ```
4. Save this as `REDIS_URL`

---

## Step 3: Deploy Backend to HuggingFace Spaces

1. Go to [https://huggingface.co/new-space](https://huggingface.co/new-space)
2. Create a new Space:
   - **Name**: `scholarmind`
   - **SDK**: `Docker`
   - **Visibility**: Public (for free tier)
   - **Hardware**: CPU Basic (free)
3. Clone the Space repo locally:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/scholarmind hf-backend
   ```
4. Copy the `backend/` contents into the Space repo:
   ```bash
   cp -r backend/* hf-backend/
   ```
5. Add secrets in HF Spaces Settings → "Variables and secrets":
   ```
   GROQ_API_KEY=gsk_your_key
   HF_TOKEN=hf_your_token
   DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/scholarmind?sslmode=require
   REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
   CORS_ORIGINS=http://localhost:3000,https://scholarmind.vercel.app,https://YOUR_USERNAME-scholarmind.hf.space
   ```
6. Push to deploy:
   ```bash
   cd hf-backend
   git add -A
   git commit -m "Deploy ScholarMind backend"
   git push
   ```
7. Wait 3-5 minutes for the Docker build. Your backend will be live at:
   ```
   https://YOUR_USERNAME-scholarmind.hf.space
   ```

---

## Step 4: Deploy Frontend to Vercel

1. Go to [https://vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
4. Add Environment Variable:
   ```
   NEXT_PUBLIC_API_URL=https://YOUR_USERNAME-scholarmind.hf.space
   ```
5. Click **Deploy**
6. Your frontend will be live at `https://scholarmind.vercel.app` (or your custom domain)

---

## Step 5: Verify Deployment

1. Open your Vercel URL → Frontend should load
2. Check the API health:
   ```
   curl https://YOUR_USERNAME-scholarmind.hf.space/api/health
   ```
3. Try a search query on the frontend
4. Check the Ops Dashboard for live metrics

---

## Environment Variables Reference

### HuggingFace Spaces (Backend)
| Variable | Required | Example |
|----------|----------|---------|
| `GROQ_API_KEY` | ✅ | `gsk_xxx` |
| `HF_TOKEN` | ✅ | `hf_xxx` |
| `DATABASE_URL` | ✅ | `postgresql://...@neon.tech/scholarmind` |
| `REDIS_URL` | Optional | `redis://...@upstash.io:6379` |
| `CORS_ORIGINS` | ✅ | `https://scholarmind.vercel.app` |
| `SCRAPE_INTERVAL_HOURS` | Optional | `6` |

### Vercel (Frontend)
| Variable | Required | Example |
|----------|----------|---------|
| `NEXT_PUBLIC_API_URL` | ✅ | `https://your-user-scholarmind.hf.space` |

---

## Troubleshooting

### HF Spaces shows "Running" but API returns 500
- Check the Logs tab in HF Spaces
- Most likely a missing secret (GROQ_API_KEY or DATABASE_URL)

### Frontend CORS errors
- Make sure `CORS_ORIGINS` in HF Spaces secrets includes your Vercel URL
- Must be exact: `https://scholarmind.vercel.app` (no trailing slash)

### Database tables not created
- The `start.sh` script runs `python -m app.seed_papers` which calls `init_database()`
- If it fails, check the HF Spaces build logs for errors

### HF Spaces goes to sleep (free tier)
- Free HF Spaces sleep after 48h of inactivity
- First request after sleep takes ~2 minutes to cold-start
- Use a free cron service (like cron-job.org) to ping `/api/health` every 30 minutes
