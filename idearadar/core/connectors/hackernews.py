"""Hacker News API connector."""
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base import BaseConnector, RawItem
import time


class HackerNewsConnector(BaseConnector):
    """Fetch items from Hacker News Firebase API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def get_name(self) -> str:
        endpoint = self.config.get("endpoint", "topstories")
        return f"HackerNews: {endpoint}"

    def fetch(self, cursor: Optional[str] = None, limit: int = 50) -> tuple[List[RawItem], Optional[str]]:
        """
        Fetch HN items.

        Cursor format: offset in the story list (e.g., "30" means start from index 30)
        """
        endpoint = self.config.get("endpoint", "topstories")
        max_limit = self.config.get("limit", 100)

        # Parse cursor (offset)
        offset = int(cursor) if cursor else 0

        # Fetch story IDs
        ids_url = f"{self.BASE_URL}/{endpoint}.json"
        response = requests.get(ids_url, timeout=10)
        response.raise_for_status()

        story_ids = response.json()

        # Slice based on offset and limit
        end_idx = min(offset + limit, len(story_ids), max_limit)
        ids_to_fetch = story_ids[offset:end_idx]

        items = []

        for story_id in ids_to_fetch:
            try:
                # Fetch story details
                story_url = f"{self.BASE_URL}/item/{story_id}.json"
                story_resp = requests.get(story_url, timeout=10)
                story_resp.raise_for_status()

                story = story_resp.json()

                if not story or story.get("deleted") or story.get("dead"):
                    continue

                # Only include stories (not jobs, polls, etc.)
                if story.get("type") not in ["story"]:
                    continue

                url = story.get("url")
                if not url:
                    # Use HN discussion URL for text posts
                    url = f"https://news.ycombinator.com/item?id={story_id}"

                pub_date = None
                if story.get("time"):
                    pub_date = datetime.fromtimestamp(story["time"])

                # Create snippet from text or title
                snippet = story.get("text", "")[:500] if story.get("text") else None

                raw_item = RawItem(
                    title=story.get("title", "Untitled"),
                    url=url,
                    published_at=pub_date,
                    author=story.get("by"),
                    source=self.get_name(),
                    snippet=snippet,
                    raw_data={
                        "hn_id": story_id,
                        "score": story.get("score", 0),
                        "descendants": story.get("descendants", 0),  # comment count
                        "type": story.get("type")
                    }
                )

                items.append(raw_item)

                # Rate limiting
                time.sleep(0.05)  # 20 requests/second max

            except Exception as e:
                print(f"Error fetching HN story {story_id}: {e}")
                continue

        # Next cursor
        next_cursor = str(end_idx) if end_idx < len(story_ids) and end_idx < max_limit else None

        return items, next_cursor
