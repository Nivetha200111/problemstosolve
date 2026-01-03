# IdeaRadar Quick Start Guide

Get IdeaRadar running in 10 minutes.

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] Git installed
- [ ] GitHub account
- [ ] Vercel account (free tier OK)
- [ ] Neon account (free tier OK) OR Supabase account

## 5-Step Deployment

### Step 1: Database Setup (2 min)

**Using Neon (Recommended):**

1. Visit [neon.tech](https://neon.tech) → Sign up → Create project
2. Click SQL Editor → Run: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Copy "Pooled connection" string → Save for later

**Using Supabase:**

1. Visit [supabase.com](https://supabase.com) → New project
2. SQL Editor → Run: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Settings → Database → Connection Pooling → Copy connection string

### Step 2: Clone & Initialize (1 min)

```bash
# Clone this repo
git clone https://github.com/YOUR_USERNAME/idearadar.git
cd idearadar

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set DATABASE_URL and CRON_SECRET
```

**Generate CRON_SECRET:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Initialize Database (1 min)

```bash
python init_db.py
```

Expected output:
```
✓ pgvector extension enabled
✓ Tables created
✓ Initial sources seeded
Database initialized successfully!
```

### Step 4: Deploy to Vercel (3 min)

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Set secrets
vercel secrets add database_url "postgresql://YOUR_CONNECTION_STRING"
vercel secrets add cron_secret "YOUR_GENERATED_SECRET"

# Deploy
vercel --prod
```

Wait for deployment → Get URL: `https://idearadar-xyz.vercel.app`

### Step 5: Trigger Ingestion (1 min)

```bash
# Replace with your actual values
VERCEL_URL="https://idearadar-xyz.vercel.app"
CRON_SECRET="your-generated-secret"

# Trigger first ingestion
curl -X POST "$VERCEL_URL/api/cron/ingest?secret=$CRON_SECRET"
```

Expected response:
```json
{
  "status": "success",
  "summary": {
    "total_processed": 156,
    "total_inserted": 145,
    "total_deduped": 11
  }
}
```

### Step 6: Verify (1 min)

Open in browser:
```
https://idearadar-xyz.vercel.app
```

Or test API:
```bash
curl "$VERCEL_URL/api/feed?sort=unique&page_size=5"
```

## Done! 🎉

Your IdeaRadar instance is now:
- ✅ Deployed and live
- ✅ Ingesting content from 6 sources
- ✅ Auto-updating every 2 hours (via cron)
- ✅ Serving a ranked feed API
- ✅ Accessible via web UI

## Next Steps

### Monitor Cron Jobs

1. Go to Vercel Dashboard → Your project
2. Click "Cron" tab
3. View execution history

### View Logs

1. Vercel Dashboard → "Logs"
2. Filter by function (e.g., `/api/cron/ingest`)

### Add More Sources

Edit `init_db.py` and add to `sources` list:

```python
{
    "name": "My Custom RSS Feed",
    "type": "rss",
    "config_json": {
        "connector": "rss",
        "url": "https://example.com/feed.xml"
    },
    "enabled": True
}
```

Then run:
```bash
python init_db.py  # Will skip existing sources
```

### Customize Scoring

Add to `.env` or Vercel environment:
```
NOVELTY_WEIGHT=0.6
QUALITY_WEIGHT=0.3
RECENCY_WEIGHT=0.1
```

Redeploy:
```bash
vercel --prod
```

### Adjust Cron Schedule

Edit `vercel.json`:
```json
"crons": [
  {
    "path": "/api/cron/ingest",
    "schedule": "0 * * * *"  // Every hour
  }
]
```

Redeploy:
```bash
vercel --prod
```

## Troubleshooting

### No items in feed?

```bash
# Manually trigger ingestion
curl -X POST "$VERCEL_URL/api/cron/ingest?secret=$CRON_SECRET"

# Check response for errors
```

### Database connection error?

1. Verify `DATABASE_URL` is correct
2. Use "Pooled connection" string (not direct)
3. Check Neon/Supabase dashboard for connection limits

### Cron not running?

1. Vercel Dashboard → Cron tab → Check status
2. Verify `CRON_SECRET` is set in Vercel environment
3. Check function logs for authentication errors

### Serverless timeout?

Reduce items per cron run:
```bash
# Add to Vercel environment variables
MAX_ITEMS_PER_CRON=30
```

## API Examples

### Get unique ideas
```bash
curl "$VERCEL_URL/api/feed?sort=unique"
```

### Search for topics
```bash
curl "$VERCEL_URL/api/search?q=machine+learning"
```

### Get item details
```bash
curl "$VERCEL_URL/api/item?id=1"
```

### Get top-scored items
```bash
curl "$VERCEL_URL/api/feed?sort=top&page_size=10"
```

### Filter by source
```bash
curl "$VERCEL_URL/api/feed?source=1"  # Hacker News
```

## Local Development

### Run ingestion locally

```bash
python -c "
from core.database import get_db
from core.ingestion import IngestionPipeline

with get_db() as db:
    pipeline = IngestionPipeline(db)
    stats = pipeline.ingest_all_sources(max_items_per_source=10)
    print(stats)
"
```

### Test connectors

```bash
python -c "
from core.connectors.hackernews import HackerNewsConnector

config = {'connector': 'hackernews', 'endpoint': 'topstories', 'limit': 5}
connector = HackerNewsConnector(config)
items, cursor = connector.fetch(limit=5)

for item in items:
    print(f'{item.title[:60]}... | Score: {item.raw_data.get(\"score\", 0)}')
"
```

### Query database

```bash
python -c "
from core.database import get_db
from core.models import Item

with get_db() as db:
    count = db.query(Item).count()
    print(f'Total items: {count}')

    top = db.query(Item).order_by(Item.final_score.desc()).limit(5).all()
    print('\nTop 5 by score:')
    for item in top:
        print(f'  {item.final_score:.3f} | {item.title[:60]}...')
"
```

## Architecture Diagram

```
┌──────────────┐
│  Vercel Cron │ (every 2 hours)
└───────┬──────┘
        │
        ▼
┌─────────────────────────┐
│ /api/cron/ingest        │
│ (authenticated)         │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Ingestion Pipeline      │
│ • Fetch (RSS/HN/arXiv)  │
│ • Extract content       │
│ • Deduplicate (SimHash) │
│ • Score (N+Q+R)         │
│ • Store in DB           │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────┐
│ PostgreSQL + pgvector   │
│ (Neon/Supabase)         │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────┐
│ API Endpoints           │
│ • GET /api/feed         │
│ • GET /api/search       │
│ • GET /api/item         │
└───────┬─────────────────┘
        │
        ▼
┌─────────────────────────┐
│ Web UI + External Apps  │
└─────────────────────────┘
```

## Resources

- **Full docs**: [README.md](README.md)
- **Deployment guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Testing guide**: [TESTING.md](TESTING.md)
- **Structure**: [STRUCTURE.md](STRUCTURE.md)

## Support

Having issues? Check:

1. [DEPLOYMENT.md](DEPLOYMENT.md) → Troubleshooting section
2. [TESTING.md](TESTING.md) → Test your setup
3. Vercel Dashboard → Logs → Function logs
4. Neon/Supabase Dashboard → Monitoring

Still stuck? Open an issue with:
- Error message
- Steps to reproduce
- Environment (Vercel logs, DB type)

---

**You're all set!** IdeaRadar is now discovering unique ideas for you. 🎯
