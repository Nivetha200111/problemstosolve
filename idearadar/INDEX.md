# IdeaRadar - Complete Index

Navigation guide to all project files and documentation.

## 📚 Documentation Files

Start here based on your goal:

| Goal | Read This | Time |
|------|-----------|------|
| **Deploy ASAP** | [QUICKSTART.md](QUICKSTART.md) | 10 min |
| **Understand architecture** | [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | 5 min |
| **Deploy to production** | [DEPLOYMENT.md](DEPLOYMENT.md) | 15 min |
| **Run tests** | [TESTING.md](TESTING.md) | 20 min |
| **Understand codebase** | [STRUCTURE.md](STRUCTURE.md) | 10 min |
| **General overview** | [README.md](README.md) | 10 min |

## 🗂️ Project Structure

```
idearadar/
├── 📖 Documentation (6 files)
│   ├── README.md              Main project documentation
│   ├── QUICKSTART.md          10-minute deployment guide
│   ├── DEPLOYMENT.md          Detailed deployment instructions
│   ├── TESTING.md             Complete test suite and examples
│   ├── STRUCTURE.md           Architecture and design decisions
│   ├── PROJECT_SUMMARY.md     Executive summary and checklist
│   └── INDEX.md               This file
│
├── ⚙️ Configuration (5 files)
│   ├── vercel.json            Vercel deployment + cron config
│   ├── requirements.txt       Python dependencies
│   ├── alembic.ini            Database migration config
│   ├── .env.example           Environment variable template
│   └── .gitignore             Git ignore rules
│
├── 🛠️ Scripts (1 file)
│   └── init_db.py             Database initialization + seeding
│
├── 🎨 Frontend (1 file)
│   └── public/
│       └── index.html         Web UI (standalone HTML/JS)
│
├── 🌐 API Endpoints (7 files)
│   └── api/
│       ├── feed.py            GET /api/feed - Ranked feed
│       ├── item.py            GET /api/item - Item details
│       ├── search.py          GET /api/search - Search items
│       ├── cron/
│       │   └── ingest.py      POST /api/cron/ingest - Scheduled ingestion
│       └── utils/
│           ├── __init__.py
│           └── response.py    Response serialization
│
└── 🔧 Core Logic (18 files)
    └── core/
        ├── config.py          Settings management
        ├── database.py        DB session management
        ├── ingestion.py       Main ingestion pipeline
        │
        ├── models/
        │   └── __init__.py    SQLAlchemy models
        │
        ├── migrations/        Alembic migrations
        │   ├── env.py
        │   ├── script.py.mako
        │   └── versions/
        │       └── .gitkeep
        │
        ├── connectors/        Source connectors
        │   ├── __init__.py    Connector factory
        │   ├── base.py        Base interface
        │   ├── rss.py         RSS connector
        │   ├── hackernews.py  HN API connector
        │   └── arxiv.py       arXiv API connector
        │
        ├── extractors/        Content extraction
        │   ├── __init__.py
        │   └── content.py     Trafilatura + BeautifulSoup
        │
        ├── dedup/             Deduplication
        │   ├── __init__.py
        │   └── simhash.py     SimHash + URL canonicalization
        │
        └── scoring/           Scoring engine
            ├── __init__.py
            └── engine.py      Novelty + Quality + Recency
```

## 📋 Quick Reference

### Installation & Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with DATABASE_URL and CRON_SECRET

# 3. Initialize database
python init_db.py

# 4. Deploy to Vercel
vercel --prod
```

See: [QUICKSTART.md](QUICKSTART.md)

### API Endpoints

| Endpoint | Method | Description | File |
|----------|--------|-------------|------|
| `/api/feed` | GET | Ranked feed | [api/feed.py](api/feed.py) |
| `/api/search` | GET | Search items | [api/search.py](api/search.py) |
| `/api/item` | GET | Item details | [api/item.py](api/item.py) |
| `/api/cron/ingest` | POST | Scheduled ingestion | [api/cron/ingest.py](api/cron/ingest.py) |

See: [README.md](README.md#api-endpoints)

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| Config | [core/config.py](core/config.py) | Environment variables, settings |
| Database | [core/database.py](core/database.py) | SQLAlchemy session management |
| Models | [core/models/__init__.py](core/models/__init__.py) | DB schema (Source, Item, etc.) |
| Ingestion | [core/ingestion.py](core/ingestion.py) | Main pipeline orchestration |
| RSS Connector | [core/connectors/rss.py](core/connectors/rss.py) | Fetch RSS feeds |
| HN Connector | [core/connectors/hackernews.py](core/connectors/hackernews.py) | Fetch from Hacker News |
| arXiv Connector | [core/connectors/arxiv.py](core/connectors/arxiv.py) | Fetch from arXiv |
| Extractor | [core/extractors/content.py](core/extractors/content.py) | Extract clean content |
| Dedup | [core/dedup/simhash.py](core/dedup/simhash.py) | SimHash deduplication |
| Scoring | [core/scoring/engine.py](core/scoring/engine.py) | Novelty/quality/recency |

See: [STRUCTURE.md](STRUCTURE.md)

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `CRON_SECRET` | Yes | - | Cron authentication secret |
| `NOVELTY_WEIGHT` | No | 0.5 | Novelty score weight |
| `QUALITY_WEIGHT` | No | 0.35 | Quality score weight |
| `RECENCY_WEIGHT` | No | 0.15 | Recency score weight |
| `MAX_ITEMS_PER_CRON` | No | 50 | Items per cron run |
| `SIMHASH_THRESHOLD` | No | 5 | Hamming distance threshold |

See: [.env.example](.env.example)

### Database Schema

```sql
sources (id, name, type, config_json, enabled, last_run_at)
  └─> items (id, url, title, scores, simhash, duplicate_of_item_id)
        └─> saved_items (collection_id, item_id)
              └─> collections (id, user_token, name)
```

See: [core/models/__init__.py](core/models/__init__.py)

### Testing

```bash
# Unit tests
python test_connectors.py
python test_extraction.py
python test_dedup.py
python test_scoring.py

# Integration tests
python test_ingestion.py

# API tests
curl "https://app.vercel.app/api/feed"
curl "https://app.vercel.app/api/search?q=AI"

# E2E tests
./e2e_test.sh
```

See: [TESTING.md](TESTING.md)

## 🎯 Use Cases

### I want to...

**...deploy IdeaRadar in 10 minutes**
→ Follow [QUICKSTART.md](QUICKSTART.md)

**...understand the architecture**
→ Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) → [STRUCTURE.md](STRUCTURE.md)

**...add a new source**
1. Edit [init_db.py](init_db.py), add to `sources` list
2. Run `python init_db.py`
3. Trigger ingestion: `curl -X POST /api/cron/ingest?secret=...`

**...add a new connector**
1. Create `core/connectors/myconnector.py`
2. Extend [BaseConnector](core/connectors/base.py)
3. Register in [core/connectors/__init__.py](core/connectors/__init__.py)
4. Add source with `"connector": "myconnector"` in config

**...customize scoring weights**
1. Edit `.env`: `NOVELTY_WEIGHT=0.6`, `QUALITY_WEIGHT=0.3`, `RECENCY_WEIGHT=0.1`
2. Redeploy: `vercel --prod`

**...change cron schedule**
1. Edit [vercel.json](vercel.json) → `crons[0].schedule`
2. Redeploy: `vercel --prod`

**...add authentication**
1. Install auth library: Add to [requirements.txt](requirements.txt)
2. Create middleware: `api/utils/auth.py`
3. Protect endpoints: Import and apply middleware

**...customize the UI**
→ Edit [public/index.html](public/index.html)

**...debug issues**
1. Check Vercel Dashboard → Logs
2. Check Database (Neon/Supabase) → Monitoring
3. See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)

**...contribute**
1. Fork repo
2. Create feature branch
3. Add tests (see [TESTING.md](TESTING.md))
4. Submit PR

## 📊 File Statistics

| Category | Files | Lines of Code |
|----------|-------|---------------|
| Documentation | 7 | ~3,500 |
| Configuration | 5 | ~150 |
| Scripts | 1 | ~100 |
| Frontend | 1 | ~350 |
| API | 5 | ~400 |
| Core Logic | 14 | ~1,800 |
| **Total** | **33** | **~6,300** |

## 🔗 External Resources

**Services:**
- [Vercel](https://vercel.com) - Hosting platform
- [Neon](https://neon.tech) - PostgreSQL database
- [Supabase](https://supabase.com) - Alternative PostgreSQL

**APIs Used:**
- [Hacker News API](https://github.com/HackerNews/API)
- [arXiv API](https://arxiv.org/help/api)
- RSS feeds (via feedparser)

**Key Libraries:**
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Trafilatura](https://trafilatura.readthedocs.io/) - Content extraction
- [SimHash](https://github.com/leonsim/simhash) - Deduplication
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity

## 🚀 Deployment Checklist

Before deploying, ensure:

- [ ] PostgreSQL database created (Neon/Supabase)
- [ ] `DATABASE_URL` configured
- [ ] `CRON_SECRET` generated and configured
- [ ] Vercel account connected to GitHub
- [ ] `python init_db.py` run successfully
- [ ] All environment variables set in Vercel

After deploying:

- [ ] Trigger initial ingestion
- [ ] Verify feed has items
- [ ] Check cron is running (Vercel Dashboard)
- [ ] Test all API endpoints
- [ ] Monitor logs for errors

See: [DEPLOYMENT.md](DEPLOYMENT.md#production-checklist)

## 💡 Tips

**Performance:**
- Keep `MAX_ITEMS_PER_CRON` ≤ 50 to avoid timeouts
- Use connection pooling URL for database
- Clean old items periodically (90-day retention)

**Cost:**
- Free tier sufficient for MVP (~1000 items/day)
- Monitor Vercel function invocations
- Monitor Neon storage usage

**Monitoring:**
- Check Vercel → Logs daily
- Monitor cron success rate
- Watch for database connection errors

**Scaling:**
- Increase `MAX_ITEMS_PER_CRON` gradually
- Add more sources incrementally
- Upgrade Neon plan if storage > 3GB

## 📞 Support

**Documentation Questions:**
→ Read relevant doc file (see table at top)

**Deployment Issues:**
→ [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)

**Code Questions:**
→ [STRUCTURE.md](STRUCTURE.md) explains all modules

**Testing Issues:**
→ [TESTING.md](TESTING.md) has examples

**Feature Requests:**
→ Open GitHub issue

**Bugs:**
→ Open GitHub issue with:
  - Error message
  - Steps to reproduce
  - Environment details

---

## 🎉 Quick Start Commands

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/idearadar.git
cd idearadar

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your DATABASE_URL and CRON_SECRET

# Initialize
python init_db.py

# Deploy
npm i -g vercel
vercel secrets add database_url "postgresql://..."
vercel secrets add cron_secret "..."
vercel --prod

# Ingest
curl -X POST "https://your-app.vercel.app/api/cron/ingest?secret=..."

# Test
curl "https://your-app.vercel.app/api/feed?sort=unique"
```

**That's it! You're live.** 🚀

---

**Last Updated**: 2026-01-03
**Version**: 1.0.0
**Status**: Production Ready ✅
