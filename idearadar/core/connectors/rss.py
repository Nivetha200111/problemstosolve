"""RSS feed connector."""
import atoma
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser
from .base import BaseConnector, RawItem


class RSSConnector(BaseConnector):
    """Fetch items from RSS feeds."""

    def get_name(self) -> str:
        return f"RSS: {self.config.get('url', 'unknown')}"

    def fetch(self, cursor: Optional[str] = None, limit: int = 50) -> tuple[List[RawItem], Optional[str]]:
        """
        Fetch RSS feed items.

        Cursor format: last_pub_timestamp (items newer than this)
        """
        url = self.config.get("url")
        if not url:
            raise ValueError("RSS connector requires 'url' in config")

        # Parse cursor (last published timestamp)
        last_pub_ts = float(cursor) if cursor else 0.0

        # Fetch feed
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Try parsing as both RSS and Atom
            try:
                feed = atoma.parse_rss_bytes(response.content)
            except:
                feed = atoma.parse_atom_bytes(response.content)
        except Exception as e:
            raise Exception(f"Failed to parse RSS/Atom feed: {e}")

        items = []
        latest_ts = last_pub_ts

        # Get entries (works for both RSS and Atom)
        entries = getattr(feed, 'items', getattr(feed, 'entries', []))

        for entry in entries[:limit]:
            # Parse published date (handle both RSS and Atom)
            pub_date = getattr(entry, 'pub_date', getattr(entry, 'published', getattr(entry, 'updated', None)))
            pub_ts = pub_date.timestamp() if pub_date else 0.0

            # Skip if older than cursor
            if pub_ts > 0 and pub_ts <= last_pub_ts:
                continue

            # Track latest timestamp
            if pub_ts > latest_ts:
                latest_ts = pub_ts

            # Extract snippet from description or content
            snippet = None
            description = getattr(entry, 'description', None)
            summary = getattr(entry, 'summary', None)
            if description:
                snippet = description[:500]
            elif summary:
                snippet = summary[:500]

            # Get author (handle different author formats)
            author = None
            author_obj = getattr(entry, 'author', None)
            if author_obj:
                if isinstance(author_obj, str):
                    author = author_obj
                elif hasattr(author_obj, 'name'):
                    author = author_obj.name

            # Get link (handle different link formats)
            link = getattr(entry, 'link', None)
            if hasattr(link, 'href'):
                link = link.href

            raw_item = RawItem(
                title=getattr(entry, 'title', "Untitled") or "Untitled",
                url=link or "",
                published_at=pub_date,
                author=author,
                source=self.get_name(),
                snippet=snippet,
                raw_data={
                    "feed_title": getattr(feed, 'title', "") or "",
                    "tags": [cat for cat in getattr(entry, 'categories', [])] if hasattr(entry, 'categories') else []
                }
            )

            if raw_item.url:  # Only add if URL exists
                items.append(raw_item)

        # Next cursor is latest timestamp seen
        next_cursor = str(latest_ts) if latest_ts > last_pub_ts else None

        return items, next_cursor
