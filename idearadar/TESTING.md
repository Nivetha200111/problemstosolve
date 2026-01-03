# IdeaRadar Testing Guide

Comprehensive test plan and example commands.

## Test Plan Overview

### Test Levels
1. **Unit Testing**: Individual components (connectors, scoring, dedup)
2. **Integration Testing**: Database operations, full ingestion pipeline
3. **API Testing**: All endpoints with various parameters
4. **End-to-End Testing**: Complete user workflows
5. **Performance Testing**: Serverless timeout, pagination, dedup performance

## Local Testing Setup

### 1. Install Dependencies

```bash
cd idearadar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Test Environment

```bash
# Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgresql://user:pass@localhost:5432/idearadar_test
CRON_SECRET=test-secret-123
NOVELTY_WEIGHT=0.5
QUALITY_WEIGHT=0.35
RECENCY_WEIGHT=0.15
MAX_ITEMS_PER_CRON=50
SIMHASH_THRESHOLD=5
EOF
```

### 3. Initialize Test Database

```bash
python init_db.py
```

## Unit Tests

### Test Connectors

#### RSS Connector
```python
# test_rss_connector.py
from core.connectors.rss import RSSConnector

config = {
    "connector": "rss",
    "url": "https://news.ycombinator.com/rss"
}

connector = RSSConnector(config)
items, cursor = connector.fetch(limit=5)

print(f"Fetched {len(items)} items")
for item in items:
    print(f"  - {item.title[:60]}... | {item.url}")

assert len(items) > 0, "Should fetch items"
assert items[0].url, "Item should have URL"
print("✓ RSS connector test passed")
```

```bash
python test_rss_connector.py
```

#### HackerNews Connector
```python
# test_hn_connector.py
from core.connectors.hackernews import HackerNewsConnector

config = {
    "connector": "hackernews",
    "endpoint": "topstories",
    "limit": 10
}

connector = HackerNewsConnector(config)
items, cursor = connector.fetch(limit=5)

print(f"Fetched {len(items)} items")
for item in items:
    print(f"  - {item.title[:60]}...")
    print(f"    Score: {item.raw_data.get('score', 0)}, Comments: {item.raw_data.get('descendants', 0)}")

assert len(items) > 0, "Should fetch items"
assert items[0].raw_data.get('hn_id'), "Should have HN ID"
print("✓ HackerNews connector test passed")
```

```bash
python test_hn_connector.py
```

#### arXiv Connector
```python
# test_arxiv_connector.py
from core.connectors.arxiv import ArxivConnector

config = {
    "connector": "arxiv",
    "search_query": "cat:cs.AI",
    "max_results": 5
}

connector = ArxivConnector(config)
items, cursor = connector.fetch(limit=5)

print(f"Fetched {len(items)} items")
for item in items:
    print(f"  - {item.title[:60]}...")
    print(f"    Authors: {item.author}")

assert len(items) > 0, "Should fetch items"
print("✓ arXiv connector test passed")
```

```bash
python test_arxiv_connector.py
```

### Test Content Extraction

```python
# test_extraction.py
from core.extractors.content import ContentExtractor

extractor = ContentExtractor()

# Test URL
url = "https://paulgraham.com/startupideas.html"
result = extractor.extract(url)

print(f"Domain: {result['domain']}")
print(f"Snippet: {result['snippet'][:100]}...")
print(f"Summary: {result['summary'][:100]}...")
print(f"Content hash: {result['content_hash']}")
print(f"Extracted text length: {len(result['extracted_text'] or '')}")

assert result['domain'], "Should extract domain"
assert result['content_hash'], "Should compute hash"
print("✓ Content extraction test passed")
```

```bash
python test_extraction.py
```

### Test Deduplication

```python
# test_dedup.py
from core.dedup import canonicalize_url, compute_simhash, hamming_distance, are_duplicates

# Test URL canonicalization
url1 = "https://example.com/article?utm_source=twitter&utm_campaign=123"
url2 = "https://Example.com/article/?ref=reddit"
canonical1 = canonicalize_url(url1)
canonical2 = canonicalize_url(url2)

print(f"URL 1: {url1}")
print(f"Canonical 1: {canonical1}")
print(f"URL 2: {url2}")
print(f"Canonical 2: {canonical2}")

assert canonical1 == canonical2, "Should canonicalize to same URL"
print("✓ URL canonicalization test passed")

# Test SimHash
text1 = "This is a test article about machine learning and artificial intelligence"
text2 = "This is a test article about machine learning and AI"  # Very similar
text3 = "Completely different article about cooking recipes"

hash1 = compute_simhash(text1)
hash2 = compute_simhash(text2)
hash3 = compute_simhash(text3)

dist_1_2 = hamming_distance(hash1, hash2)
dist_1_3 = hamming_distance(hash1, hash3)

print(f"\nSimHash 1: {hash1}")
print(f"SimHash 2: {hash2}")
print(f"SimHash 3: {hash3}")
print(f"Distance 1-2: {dist_1_2}")
print(f"Distance 1-3: {dist_1_3}")
print(f"Are 1 and 2 duplicates? {are_duplicates(hash1, hash2)}")
print(f"Are 1 and 3 duplicates? {are_duplicates(hash1, hash3)}")

assert dist_1_2 < dist_1_3, "Similar texts should have smaller distance"
print("✓ SimHash test passed")
```

```bash
python test_dedup.py
```

### Test Scoring

```python
# test_scoring.py
from core.database import get_db
from core.scoring import ScoringEngine
from datetime import datetime, timedelta

with get_db() as db:
    scorer = ScoringEngine(db)

    # Test novelty (random simhash should be very novel)
    novelty = scorer.compute_novelty_score(simhash=123456789)
    print(f"Novelty score (first item): {novelty:.3f}")
    assert novelty >= 0.8, "First item should be highly novel"

    # Test quality
    quality = scorer.compute_quality_score(
        raw_signals={"score": 150, "descendants": 75},
        source_id=1,
        extracted_text="A" * 1000
    )
    print(f"Quality score (HN, high engagement): {quality:.3f}")
    assert quality > 0.5, "High quality item should score well"

    # Test recency
    recent = scorer.compute_recency_score(datetime.utcnow() - timedelta(hours=1))
    old = scorer.compute_recency_score(datetime.utcnow() - timedelta(days=7))
    print(f"Recency score (1 hour ago): {recent:.3f}")
    print(f"Recency score (7 days ago): {old:.3f}")
    assert recent > old, "Recent items should score higher"

    # Test final score
    scores = scorer.score_item(
        simhash=987654321,
        published_at=datetime.utcnow() - timedelta(hours=2),
        raw_signals={"score": 100},
        source_id=1,
        extracted_text="Test content",
        domain="example.com"
    )
    print(f"\nFinal scores: {scores}")
    assert 0 <= scores['final_score'] <= 1, "Final score should be 0-1"

print("✓ Scoring test passed")
```

```bash
python test_scoring.py
```

## Integration Tests

### Test Full Ingestion Pipeline

```python
# test_ingestion.py
from core.database import get_db
from core.ingestion import IngestionPipeline
from core.models import Source, Item

with get_db() as db:
    # Get a source
    source = db.query(Source).filter_by(name="Hacker News Top Stories").first()

    if not source:
        print("! No sources found. Run init_db.py first.")
        exit(1)

    # Run ingestion
    pipeline = IngestionPipeline(db)
    stats = pipeline.ingest_source(source, max_items=10)

    print(f"Ingestion stats:")
    print(f"  Processed: {stats['processed']}")
    print(f"  Inserted: {stats['inserted']}")
    print(f"  Deduped: {stats['deduped']}")
    print(f"  Errors: {len(stats['errors'])}")

    # Check items were created
    items = db.query(Item).limit(5).all()
    print(f"\nSample items:")
    for item in items:
        print(f"  - {item.title[:60]}... (score: {item.final_score:.3f})")

    assert stats['processed'] > 0, "Should process items"
    print("\n✓ Ingestion test passed")
```

```bash
python test_ingestion.py
```

## API Tests

### Using curl

#### Test Feed Endpoint

**Basic feed:**
```bash
curl -X GET "http://localhost:3000/api/feed" | jq
```

**Expected response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Example Article",
      "url": "https://example.com/article",
      "domain": "example.com",
      "scores": {
        "novelty": 0.85,
        "quality": 0.72,
        "final": 0.78
      },
      ...
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 145,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

**Sort by unique:**
```bash
curl "http://localhost:3000/api/feed?sort=unique&page_size=5" | jq '.items[] | {title, scores}'
```

**Sort by top:**
```bash
curl "http://localhost:3000/api/feed?sort=top&page_size=5" | jq '.items[] | {title, scores}'
```

**Filter by source:**
```bash
curl "http://localhost:3000/api/feed?source=1&page_size=5" | jq
```

**Filter by topic:**
```bash
curl "http://localhost:3000/api/feed?topic=machine+learning" | jq '.pagination'
```

**Pagination:**
```bash
curl "http://localhost:3000/api/feed?page=2&page_size=10" | jq '.pagination'
```

#### Test Item Endpoint

**Get item by ID:**
```bash
curl "http://localhost:3000/api/item?id=1" | jq
```

**Expected response:**
```json
{
  "id": 1,
  "title": "Example Article",
  "url": "https://example.com/article",
  "domain": "example.com",
  "published_at": "2024-01-15T10:30:00",
  "snippet": "Article snippet...",
  "summary": "Article summary...",
  "source": {
    "id": 1,
    "name": "Hacker News Top Stories"
  },
  "scores": {
    "novelty": 0.85,
    "quality": 0.72,
    "final": 0.78
  },
  "signals": {
    "score": 150,
    "descendants": 45
  },
  "why_unique": [
    "High content novelty compared to recent items",
    "High quality signals (source, engagement, content)",
    "High engagement: 150 points"
  ],
  "is_duplicate": false
}
```

**Invalid ID:**
```bash
curl "http://localhost:3000/api/item?id=999999" | jq
```

**Expected:** 404 error

#### Test Search Endpoint

**Basic search:**
```bash
curl "http://localhost:3000/api/search?q=machine+learning" | jq '.items | length'
```

**Search with sort:**
```bash
curl "http://localhost:3000/api/search?q=AI&sort=unique" | jq '.items[] | {title, scores}'
```

**Search with pagination:**
```bash
curl "http://localhost:3000/api/search?q=startup&page=1&page_size=5" | jq '.pagination'
```

**Empty search:**
```bash
curl "http://localhost:3000/api/search?q=" | jq
```

**Expected:** 400 error

#### Test Cron Endpoint

**With correct secret:**
```bash
curl -X POST -H "X-Cron-Secret: test-secret-123" \
  "http://localhost:3000/api/cron/ingest" | jq
```

**Expected response:**
```json
{
  "status": "success",
  "summary": {
    "total_processed": 156,
    "total_inserted": 145,
    "total_deduped": 11,
    "total_errors": 0
  },
  "sources": [
    {
      "source_id": 1,
      "source_name": "Hacker News Top Stories",
      "processed": 30,
      "inserted": 28,
      "deduped": 2,
      "errors": []
    }
  ]
}
```

**With query param:**
```bash
curl -X POST "http://localhost:3000/api/cron/ingest?secret=test-secret-123" | jq
```

**Without secret:**
```bash
curl -X POST "http://localhost:3000/api/cron/ingest" | jq
```

**Expected:** 401 error

## Performance Tests

### Test Serverless Timeout Limits

```python
# test_performance.py
import time
from core.database import get_db
from core.ingestion import IngestionPipeline
from core.models import Source

# Test ingestion speed
with get_db() as db:
    source = db.query(Source).first()
    pipeline = IngestionPipeline(db)

    # Time the ingestion
    start = time.time()
    stats = pipeline.ingest_source(source, max_items=50)
    elapsed = time.time() - start

    print(f"Ingested {stats['processed']} items in {elapsed:.2f}s")
    print(f"Average: {elapsed/stats['processed']:.2f}s per item")
    print(f"Serverless safe? {elapsed < 60} (Vercel limit: 60s)")

    assert elapsed < 60, "Should complete within serverless limit"
    print("✓ Performance test passed")
```

### Test Pagination Performance

```bash
# Test large page
curl -w "Time: %{time_total}s\n" \
  "http://localhost:3000/api/feed?page=1&page_size=100" -o /dev/null -s

# Test deep pagination
curl -w "Time: %{time_total}s\n" \
  "http://localhost:3000/api/feed?page=10&page_size=20" -o /dev/null -s
```

### Test Deduplication Performance

```python
# test_dedup_performance.py
import time
from core.database import get_db
from core.models import Item
from core.dedup import compute_simhash, hamming_distance

with get_db() as db:
    # Get all items
    items = db.query(Item).filter(Item.simhash.isnot(None)).limit(1000).all()

    print(f"Testing dedup with {len(items)} items")

    # Test simhash computation
    test_text = "This is a test article" * 100
    start = time.time()
    for _ in range(100):
        compute_simhash(test_text)
    elapsed = time.time() - start
    print(f"SimHash computation: {elapsed/100*1000:.2f}ms per hash")

    # Test hamming distance
    if len(items) >= 2:
        hash1 = items[0].simhash
        start = time.time()
        for item in items[:100]:
            hamming_distance(hash1, item.simhash)
        elapsed = time.time() - start
        print(f"Hamming distance: {elapsed/100*1000:.2f}ms per comparison")

    print("✓ Dedup performance test passed")
```

## End-to-End Tests

### Complete User Workflow

```bash
#!/bin/bash
# e2e_test.sh

BASE_URL="http://localhost:3000"
SECRET="test-secret-123"

echo "=== IdeaRadar E2E Test ==="

echo -e "\n1. Trigger ingestion..."
curl -X POST -H "X-Cron-Secret: $SECRET" "$BASE_URL/api/cron/ingest" | jq '.summary'

echo -e "\n2. Get feed (most unique)..."
curl "$BASE_URL/api/feed?sort=unique&page_size=3" | jq '.items[] | {title, scores}'

echo -e "\n3. Search for 'AI'..."
curl "$BASE_URL/api/search?q=AI&page_size=3" | jq '.items[] | {title}'

echo -e "\n4. Get item detail..."
ITEM_ID=$(curl -s "$BASE_URL/api/feed?page_size=1" | jq -r '.items[0].id')
curl "$BASE_URL/api/item?id=$ITEM_ID" | jq '{title, why_unique}'

echo -e "\n✓ E2E test complete"
```

```bash
chmod +x e2e_test.sh
./e2e_test.sh
```

## Production Tests

### Test on Vercel

Replace `localhost:3000` with your Vercel URL in all curl commands:

```bash
VERCEL_URL="https://idearadar-abc123.vercel.app"
CRON_SECRET="your-production-secret"

# Test feed
curl "$VERCEL_URL/api/feed?sort=unique" | jq '.pagination'

# Test search
curl "$VERCEL_URL/api/search?q=startup" | jq '.items | length'

# Test cron (authenticated)
curl -X POST -H "X-Cron-Secret: $CRON_SECRET" "$VERCEL_URL/api/cron/ingest" | jq '.summary'
```

## Test Checklist

**Before Deployment:**
- [ ] All connectors fetch data successfully
- [ ] Content extraction works on sample URLs
- [ ] Deduplication detects similar content
- [ ] Scoring produces reasonable values (0-1 range)
- [ ] Database initialization creates all tables
- [ ] Ingestion pipeline inserts items correctly

**After Deployment:**
- [ ] `/api/feed` returns items
- [ ] `/api/feed` pagination works
- [ ] `/api/feed` sorting works (unique/top/new)
- [ ] `/api/search` finds relevant items
- [ ] `/api/item` returns item details
- [ ] `/api/item` includes "why_unique" explanations
- [ ] `/api/cron/ingest` requires authentication
- [ ] `/api/cron/ingest` processes items successfully
- [ ] Cron runs automatically (check after 2 hours)
- [ ] UI loads and displays items
- [ ] UI search works
- [ ] UI pagination works

**Performance:**
- [ ] Ingestion completes within 60 seconds
- [ ] API responses < 2 seconds
- [ ] No database connection errors
- [ ] Deduplication handles 1000+ items efficiently

## Continuous Testing

Create a monitoring script:

```bash
# monitor.sh
#!/bin/bash

VERCEL_URL="https://idearadar-abc123.vercel.app"

while true; do
  echo "$(date): Testing endpoints..."

  # Test feed
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$VERCEL_URL/api/feed")
  echo "  Feed: $STATUS"

  # Test search
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$VERCEL_URL/api/search?q=test")
  echo "  Search: $STATUS"

  sleep 300  # Every 5 minutes
done
```

---

**Testing complete!** ✓

All tests should pass before deploying to production.
