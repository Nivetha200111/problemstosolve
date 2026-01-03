# IdeaRadar 🎯

**Unique-Idea Web Discovery Tool**

IdeaRadar is a Python-based web discovery tool that ingests content from multiple sources (RSS, APIs), extracts and deduplicates content, computes novelty and quality scores, and serves a ranked feed of the most unique and interesting ideas via a REST API.

## Features

- **Multi-source ingestion**: RSS feeds, Hacker News, arXiv
- **Smart deduplication**: SimHash-based near-duplicate detection
- **Intelligent scoring**: Novelty (50%) + Quality (35%) + Recency (15%)
- **REST API**: Feed, search, and item endpoints
- **Scheduled updates**: Vercel Cron for automatic ingestion
- **Minimal UI**: Clean, responsive web interface

## Architecture

- **Backend**: Python serverless functions (Vercel)
- **Database**: PostgreSQL with pgvector (Neon/Supabase)
- **ORM**: SQLAlchemy + Alembic
- **Ingestion**: Pluggable connector architecture
- **Extraction**: Trafilatura + BeautifulSoup
- **Deduplication**: SimHash + optional vector embeddings

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL database (Neon or Supabase recommended)
- Vercel account (for deployment)

### Local Setup

1. **Clone and install dependencies**

```bash
git clone <your-repo-url>
cd idearadar
pip install -r requirements.txt
```

2. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your database URL and secrets
```

3. **Initialize database**

```bash
python init_db.py
```

4. **Run locally** (optional - for testing)

```bash
# Test ingestion
python -c "from core.database import get_db; from core.ingestion import IngestionPipeline; \
with get_db() as db: IngestionPipeline(db).ingest_all_sources()"

# Or run API locally with Flask (requires flask installation)
# Note: For production, deploy to Vercel
```

### Deployment to Vercel

1. **Install Vercel CLI**

```bash
npm i -g vercel
```

2. **Set up Vercel secrets**

```bash
vercel secrets add database_url "postgresql://user:pass@host:5432/db"
vercel secrets add cron_secret "your-random-secret-token"
```

3. **Deploy**

```bash
vercel --prod
```

4. **Initialize database on first deploy**

After deployment, run the init script once:

```bash
# SSH into your server or run locally with production DATABASE_URL
python init_db.py
```

5. **Trigger initial ingestion**

```bash
curl -X POST "https://your-app.vercel.app/api/cron/ingest?secret=your-cron-secret"
```

## Database Setup

### Using Neon (Recommended)

1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new project
3. Enable pgvector extension in SQL Editor:
   ```sql
   CREATE EXTENSION vector;
   ```
4. Copy connection string and set as `DATABASE_URL`

### Using Supabase

1. Go to [supabase.com](https://supabase.com) and create a project
2. Enable pgvector in SQL Editor:
   ```sql
   CREATE EXTENSION vector;
   ```
3. Get connection string from Settings → Database
4. Set as `DATABASE_URL` (use connection pooling URL for serverless)

## API Endpoints

### GET /api/feed

Get ranked feed of items.

**Query Parameters:**
- `sort`: `unique` | `top` | `new` (default: `unique`)
- `topic`: Filter by keyword
- `source`: Filter by source ID
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Example:**
```bash
curl "https://your-app.vercel.app/api/feed?sort=unique&page=1"
```

### GET /api/item

Get single item by ID.

**Query Parameters:**
- `id`: Item ID (required)

**Example:**
```bash
curl "https://your-app.vercel.app/api/item?id=123"
```

### GET /api/search

Search items.

**Query Parameters:**
- `q`: Search query (required)
- `sort`: `unique` | `relevance` (default: `relevance`)
- `page`: Page number
- `page_size`: Items per page

**Example:**
```bash
curl "https://your-app.vercel.app/api/search?q=machine+learning&sort=unique"
```

### POST /api/cron/ingest

Scheduled ingestion endpoint (protected).

**Authentication:**
- Header: `X-Cron-Secret: your-secret`
- OR Query param: `?secret=your-secret`

**Example:**
```bash
curl -X POST -H "X-Cron-Secret: your-secret" \
  "https://your-app.vercel.app/api/cron/ingest"
```

## Configuration

All configuration is via environment variables. See `.env.example` for full list.

**Required:**
- `DATABASE_URL`: PostgreSQL connection string
- `CRON_SECRET`: Secret for protecting cron endpoint

**Optional:**
- `NOVELTY_WEIGHT`: Novelty score weight (default: 0.5)
- `QUALITY_WEIGHT`: Quality score weight (default: 0.35)
- `RECENCY_WEIGHT`: Recency score weight (default: 0.15)
- `MAX_ITEMS_PER_CRON`: Max items per cron run (default: 50)
- `CONTENT_MAX_LENGTH`: Max content length to store (default: 10000)

## Sources

Initial sources are seeded automatically:

1. Hacker News Top Stories (API)
2. arXiv CS.AI Recent Papers (API)
3. arXiv CS.LG Recent Papers (API)
4. TechCrunch RSS
5. MIT News AI RSS
6. Product Hunt RSS

Add more sources by inserting into the `sources` table.

## Scoring Algorithm

**Final Score = 0.5 × Novelty + 0.35 × Quality + 0.15 × Recency**

- **Novelty**: Computed via SimHash Hamming distance to recent items
- **Quality**: Based on source weight, engagement (HN points/comments), content heuristics
- **Recency**: Exponential decay with 24-hour half-life

## Compliance & Ethics

- Respects `robots.txt` (via allowlisting)
- Only stores snippets/summaries (not full copyrighted text)
- Includes attribution (source + URL + domain)
- No scraping of paywalled content
- Rate limiting per domain

## Serverless Constraints

- **Cron timeout**: Each run processes max 50 items per source
- **Cursor-based**: Ingestion is resumable across runs
- **Idempotent**: Running cron multiple times won't create duplicates
- **Connection pooling**: Optimized for serverless DB connections

## Testing

**Test feed endpoint:**
```bash
curl "http://localhost:3000/api/feed"
```

**Test search:**
```bash
curl "http://localhost:3000/api/search?q=AI"
```

**Test ingestion:**
```bash
curl -X POST "http://localhost:3000/api/cron/ingest?secret=change-me-in-production"
```

## Troubleshooting

**Database connection errors:**
- Verify `DATABASE_URL` is correct
- For Neon/Supabase, use connection pooling URL
- Check connection limits (serverless uses many connections)

**Cron not running:**
- Verify cron is configured in `vercel.json`
- Check Vercel dashboard → Cron tab
- Ensure `CRON_SECRET` is set in Vercel environment

**No items appearing:**
- Run cron endpoint manually to trigger ingestion
- Check logs for errors
- Verify sources are enabled in database

## Project Structure

```
idearadar/
├── api/                    # Vercel serverless functions
│   ├── cron/
│   │   └── ingest.py      # Cron ingestion endpoint
│   ├── utils/
│   │   └── response.py    # Response utilities
│   ├── feed.py            # Feed endpoint
│   ├── item.py            # Item detail endpoint
│   └── search.py          # Search endpoint
├── core/                   # Core business logic
│   ├── connectors/        # Source connectors
│   │   ├── base.py
│   │   ├── rss.py
│   │   ├── hackernews.py
│   │   └── arxiv.py
│   ├── dedup/             # Deduplication
│   │   └── simhash.py
│   ├── extractors/        # Content extraction
│   │   └── content.py
│   ├── migrations/        # Alembic migrations
│   ├── models/            # Database models
│   │   └── __init__.py
│   ├── scoring/           # Scoring engine
│   │   └── engine.py
│   ├── config.py          # Configuration
│   ├── database.py        # Database session
│   └── ingestion.py       # Ingestion pipeline
├── public/                 # Static UI
│   └── index.html
├── .env.example
├── .gitignore
├── alembic.ini
├── init_db.py             # Database initialization
├── README.md
├── requirements.txt
└── vercel.json
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
