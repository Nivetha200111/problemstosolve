"""Initialize database schema and seed sources."""
import sys
from sqlalchemy import text
from core.database import engine, get_db
from core.models import Base, Source
from datetime import datetime


def init_database():
    """Create all tables and seed initial sources."""
    print("Creating database tables...")

    # Enable pgvector extension if available
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("✓ pgvector extension enabled")
    except Exception as e:
        print(f"! pgvector not available (will use SimHash only): {e}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")

    # Seed initial sources
    seed_sources()
    print("✓ Initial sources seeded")
    print("\nDatabase initialized successfully!")


def seed_sources():
    """Seed initial content sources."""
    sources = [
        {
            "name": "Hacker News Top Stories",
            "type": "api",
            "config_json": {
                "connector": "hackernews",
                "endpoint": "topstories",
                "limit": 30
            },
            "enabled": True
        },
        {
            "name": "arXiv CS.AI Recent",
            "type": "api",
            "config_json": {
                "connector": "arxiv",
                "search_query": "cat:cs.AI",
                "max_results": 20,
                "sort_by": "submittedDate",
                "sort_order": "descending"
            },
            "enabled": True
        },
        {
            "name": "arXiv CS.LG Recent",
            "type": "api",
            "config_json": {
                "connector": "arxiv",
                "search_query": "cat:cs.LG",
                "max_results": 20,
                "sort_by": "submittedDate",
                "sort_order": "descending"
            },
            "enabled": True
        },
        {
            "name": "TechCrunch RSS",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://techcrunch.com/feed/"
            },
            "enabled": True
        },
        {
            "name": "MIT News AI RSS",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://news.mit.edu/rss/topic/artificial-intelligence2"
            },
            "enabled": True
        },
        {
            "name": "Product Hunt RSS",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://www.producthunt.com/feed"
            },
            "enabled": True
        }
    ]

    with get_db() as db:
        for source_data in sources:
            # Check if source already exists
            existing = db.query(Source).filter_by(name=source_data["name"]).first()
            if not existing:
                source = Source(**source_data)
                db.add(source)
                print(f"  + Added source: {source_data['name']}")
            else:
                print(f"  - Source already exists: {source_data['name']}")


if __name__ == "__main__":
    init_database()
