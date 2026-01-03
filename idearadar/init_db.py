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
    """Seed initial content sources focused on developer project ideas."""
    sources = [
        {
            "name": "Hacker News Show HN",
            "type": "api",
            "config_json": {
                "connector": "hackernews",
                "endpoint": "showstories",
                "limit": 50
            },
            "enabled": True
        },
        {
            "name": "Product Hunt - New Products",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://www.producthunt.com/feed"
            },
            "enabled": True
        },
        {
            "name": "GitHub Trending Repositories",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml"
            },
            "enabled": True
        },
        {
            "name": "Dev.to Top Posts",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://dev.to/feed/top/week"
            },
            "enabled": True
        },
        {
            "name": "Indie Hackers Projects",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://www.indiehackers.com/feed.xml"
            },
            "enabled": True
        },
        {
            "name": "Reddit r/SideProject",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://www.reddit.com/r/SideProject/.rss"
            },
            "enabled": True
        },
        {
            "name": "Reddit r/webdev Projects",
            "type": "rss",
            "config_json": {
                "connector": "rss",
                "url": "https://www.reddit.com/r/webdev/.rss"
            },
            "enabled": True
        },
        {
            "name": "arXiv CS.SE (Software Engineering)",
            "type": "api",
            "config_json": {
                "connector": "arxiv",
                "search_query": "cat:cs.SE",
                "max_results": 15,
                "sort_by": "submittedDate",
                "sort_order": "descending"
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
