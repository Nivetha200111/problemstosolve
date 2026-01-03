# IdeaRadar Deployment Guide

Complete step-by-step guide to deploy IdeaRadar to Vercel.

## Prerequisites

- GitHub account
- Vercel account (sign up at [vercel.com](https://vercel.com))
- PostgreSQL database (we'll use Neon's free tier)

## Step 1: Set Up Database (Neon)

### 1.1 Create Neon Account

1. Go to [neon.tech](https://neon.tech)
2. Sign up with GitHub
3. Click "Create a project"

### 1.2 Configure Database

1. **Project settings:**
   - Name: `idearadar`
   - Region: Choose closest to your users
   - Postgres version: 15 or 16

2. **Enable pgvector:**
   - Click "SQL Editor" in sidebar
   - Run this SQL:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
   - Click "Run" or press Ctrl+Enter

3. **Get connection string:**
   - Click "Dashboard"
   - Copy the connection string (looks like: `postgresql://user:pass@host/db`)
   - **Important**: Use the "Pooled connection" string for serverless
   - Save this for later

### Alternative: Supabase

If you prefer Supabase:

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. In SQL Editor, run: `CREATE EXTENSION IF NOT EXISTS vector;`
4. Go to Settings → Database → Connection Pooling
5. Copy "Connection string" (Transaction mode)

## Step 2: Push Code to GitHub

### 2.1 Initialize Git Repository

```bash
cd idearadar
git init
git add .
git commit -m "Initial commit: IdeaRadar MVP"
```

### 2.2 Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `idearadar`
3. Make it Public or Private
4. Don't initialize with README (we already have one)
5. Click "Create repository"

### 2.3 Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/idearadar.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Vercel

### 3.1 Import Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click "Import" next to your GitHub repository
3. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (leave as is)
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)

### 3.2 Add Environment Variables

Click "Environment Variables" and add:

| Name | Value | Environment |
|------|-------|-------------|
| `DATABASE_URL` | Your Neon connection string | Production, Preview, Development |
| `CRON_SECRET` | Random secret (generate one) | Production, Preview, Development |

**Generate CRON_SECRET:**
```bash
# On macOS/Linux:
openssl rand -base64 32

# Or use this Python one-liner:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Optional variables:**
- `NOVELTY_WEIGHT`: 0.5
- `QUALITY_WEIGHT`: 0.35
- `RECENCY_WEIGHT`: 0.15
- `MAX_ITEMS_PER_CRON`: 50

### 3.3 Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for deployment
3. You'll get a URL like: `https://idearadar-abc123.vercel.app`

## Step 4: Initialize Database

### 4.1 Install Dependencies Locally

```bash
cd idearadar
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4.2 Set Environment Variable

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=your_neon_connection_string_here
CRON_SECRET=your_generated_secret_here
EOF
```

### 4.3 Run Database Initialization

```bash
python init_db.py
```

You should see:
```
Creating database tables...
✓ pgvector extension enabled
✓ Tables created
  + Added source: Hacker News Top Stories
  + Added source: arXiv CS.AI Recent
  + Added source: arXiv CS.LG Recent
  + Added source: TechCrunch RSS
  + Added source: MIT News AI RSS
  + Added source: Product Hunt RSS
✓ Initial sources seeded

Database initialized successfully!
```

## Step 5: Trigger First Ingestion

### 5.1 Manual Trigger

```bash
curl -X POST "https://YOUR_APP.vercel.app/api/cron/ingest?secret=YOUR_CRON_SECRET"
```

**Replace:**
- `YOUR_APP.vercel.app` with your actual Vercel URL
- `YOUR_CRON_SECRET` with your actual secret

### 5.2 Verify Ingestion

Response should look like:
```json
{
  "status": "success",
  "summary": {
    "total_processed": 156,
    "total_inserted": 145,
    "total_deduped": 11,
    "total_errors": 0
  },
  "sources": [...]
}
```

### 5.3 Check Feed

Open in browser or curl:
```bash
curl "https://YOUR_APP.vercel.app/api/feed?sort=unique&page=1"
```

## Step 6: Configure Cron (Automatic Updates)

Vercel Cron is already configured in `vercel.json` to run every 2 hours.

### 6.1 Verify Cron Configuration

1. Go to Vercel dashboard
2. Select your project
3. Go to "Cron" tab
4. You should see: `/api/cron/ingest` running every `0 */2 * * *` (every 2 hours)

### 6.2 View Cron Logs

1. In Vercel dashboard → Cron tab
2. Click on the cron job
3. View execution history and logs

### 6.3 Adjust Cron Schedule (Optional)

Edit `vercel.json`:
```json
"crons": [
  {
    "path": "/api/cron/ingest",
    "schedule": "0 */2 * * *"  // Change this
  }
]
```

**Common schedules:**
- Every hour: `0 * * * *`
- Every 6 hours: `0 */6 * * *`
- Daily at midnight: `0 0 * * *`
- Every 30 minutes: `*/30 * * * *`

Then redeploy:
```bash
vercel --prod
```

## Step 7: Test Your Deployment

### 7.1 Test Web UI

1. Open `https://YOUR_APP.vercel.app` in browser
2. You should see the IdeaRadar interface
3. Items should load automatically
4. Try sorting by "Most Unique", "Top Scored", "Most Recent"
5. Try searching for keywords

### 7.2 Test API Endpoints

**Feed:**
```bash
curl "https://YOUR_APP.vercel.app/api/feed?sort=unique&page_size=5" | jq
```

**Search:**
```bash
curl "https://YOUR_APP.vercel.app/api/search?q=machine+learning" | jq
```

**Item detail:**
```bash
# Replace 1 with actual item ID from feed
curl "https://YOUR_APP.vercel.app/api/item?id=1" | jq
```

**Cron (authenticated):**
```bash
curl -X POST -H "X-Cron-Secret: YOUR_SECRET" \
  "https://YOUR_APP.vercel.app/api/cron/ingest" | jq
```

## Step 8: Monitor and Maintain

### 8.1 View Logs

1. Vercel Dashboard → Your project
2. Click "Logs" tab
3. Filter by function (`/api/feed`, `/api/cron/ingest`, etc.)

### 8.2 Monitor Database

**Neon:**
1. Neon Dashboard → Your project
2. Click "Monitoring" to see:
   - Connection count
   - Query performance
   - Database size

**Check item count:**
```sql
SELECT COUNT(*) FROM items;
SELECT COUNT(*) FROM items WHERE duplicate_of_item_id IS NULL;
```

### 8.3 Common Maintenance Tasks

**Add a new source:**
```sql
INSERT INTO sources (name, type, config_json, enabled, created_at)
VALUES (
  'New RSS Feed',
  'rss',
  '{"connector": "rss", "url": "https://example.com/feed.xml"}',
  true,
  NOW()
);
```

**Disable a source:**
```sql
UPDATE sources SET enabled = false WHERE name = 'Source Name';
```

**Clean old items (keep last 90 days):**
```sql
DELETE FROM items
WHERE created_at < NOW() - INTERVAL '90 days';
```

## Troubleshooting

### Issue: Database connection timeout

**Solution:**
- Use Neon's "Pooled connection" string (not direct)
- Check connection limit in Neon dashboard
- Consider upgrading Neon plan if hitting limits

### Issue: Cron not running

**Solution:**
1. Check Vercel → Cron tab for errors
2. Verify `CRON_SECRET` is set in environment
3. Check function logs for authentication errors
4. Manually trigger to test: `curl -X POST ...`

### Issue: No items in feed

**Solution:**
1. Check if cron has run: `SELECT last_run_at FROM sources;`
2. Manually trigger ingestion
3. Check logs for errors during ingestion
4. Verify sources are enabled: `SELECT * FROM sources WHERE enabled = true;`

### Issue: Serverless timeout

**Solution:**
- Reduce `MAX_ITEMS_PER_CRON` (default: 50)
- Set to 20 or 30 for slower sources
- Add environment variable: `MAX_ITEMS_PER_CRON=30`

### Issue: Duplicate items still appearing

**Solution:**
- Check `simhash` values are being computed
- Adjust `SIMHASH_THRESHOLD` (default: 5)
- Lower threshold (3-4) for stricter dedup
- Higher threshold (6-8) for looser dedup

## Production Checklist

- [ ] Database initialized with sources
- [ ] Environment variables set in Vercel
- [ ] First ingestion completed successfully
- [ ] Feed loads with items
- [ ] Search works
- [ ] Cron configured and running
- [ ] Custom domain configured (optional)
- [ ] Analytics added (optional)
- [ ] Error monitoring set up (optional)

## Optional: Custom Domain

1. Vercel Dashboard → Your project → Settings → Domains
2. Add your domain (e.g., `idearadar.yourdomain.com`)
3. Follow DNS configuration instructions
4. Wait for SSL certificate (automatic)

## Optional: Analytics

### Vercel Analytics

1. Vercel Dashboard → Your project → Analytics
2. Click "Enable"
3. Free tier includes 100k events/month

### Custom Analytics

Add to `public/index.html` before `</head>`:
```html
<!-- Google Analytics, Plausible, etc. -->
```

## Cost Estimate

**Free Tier:**
- Vercel: Free (100GB bandwidth, 100 serverless function executions/day)
- Neon: Free (3GB storage, 1 compute unit)
- **Total: $0/month**

**If you exceed free tier:**
- Vercel Pro: $20/month (unlimited functions)
- Neon Pro: $19/month (10GB storage, autoscaling)
- **Total: ~$40/month**

## Next Steps

1. **Add more sources**: Edit `init_db.py` or insert via SQL
2. **Customize scoring**: Adjust weights in `.env`
3. **Add authentication**: Implement user login for collections
4. **Improve UI**: Customize `public/index.html`
5. **Add vector embeddings**: Set up embedding API for semantic dedup

## Support

- Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/idearadar/issues)
- Docs: [README.md](README.md)

---

**Deployment complete!** 🎉

Your IdeaRadar instance should now be live and automatically ingesting unique ideas every 2 hours.
