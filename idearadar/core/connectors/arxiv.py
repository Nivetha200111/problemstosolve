"""arXiv API connector."""
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser
from xml.etree import ElementTree as ET
from .base import BaseConnector, RawItem
import time
import urllib.parse


class ArxivConnector(BaseConnector):
    """Fetch papers from arXiv API."""

    BASE_URL = "http://export.arxiv.org/api/query"

    def get_name(self) -> str:
        query = self.config.get("search_query", "all")
        return f"arXiv: {query}"

    def fetch(self, cursor: Optional[str] = None, limit: int = 50) -> tuple[List[RawItem], Optional[str]]:
        """
        Fetch arXiv papers.

        Cursor format: start index for pagination
        """
        search_query = self.config.get("search_query", "all")
        max_results = min(limit, self.config.get("max_results", 100))
        sort_by = self.config.get("sort_by", "submittedDate")
        sort_order = self.config.get("sort_order", "descending")

        # Parse cursor (start index)
        start = int(cursor) if cursor else 0

        # Build query parameters
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }

        # Fetch from arXiv API
        response = requests.get(self.BASE_URL, params=params, timeout=15)
        response.raise_for_status()

        # Parse XML response
        root = ET.fromstring(response.content)

        # arXiv API uses Atom namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        items = []

        for entry in root.findall("atom:entry", ns):
            try:
                # Extract fields
                title_elem = entry.find("atom:title", ns)
                title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else "Untitled"

                # Get arXiv ID and URL
                id_elem = entry.find("atom:id", ns)
                url = id_elem.text if id_elem is not None else None

                # Published date
                published_elem = entry.find("atom:published", ns)
                pub_date = None
                if published_elem is not None:
                    try:
                        pub_date = date_parser.parse(published_elem.text)
                    except:
                        pass

                # Authors
                authors = []
                for author_elem in entry.findall("atom:author", ns):
                    name_elem = author_elem.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)

                author = ", ".join(authors) if authors else None

                # Summary (abstract)
                summary_elem = entry.find("atom:summary", ns)
                snippet = None
                if summary_elem is not None:
                    snippet = summary_elem.text.strip().replace("\n", " ")[:1000]

                # Categories
                categories = []
                for cat_elem in entry.findall("atom:category", ns):
                    term = cat_elem.get("term")
                    if term:
                        categories.append(term)

                raw_item = RawItem(
                    title=title,
                    url=url,
                    published_at=pub_date,
                    author=author,
                    source=self.get_name(),
                    snippet=snippet,
                    raw_data={
                        "categories": categories,
                        "arxiv_id": url.split("/")[-1] if url else None
                    }
                )

                if raw_item.url:
                    items.append(raw_item)

            except Exception as e:
                print(f"Error parsing arXiv entry: {e}")
                continue

        # Rate limiting (arXiv asks for 3 seconds between requests)
        time.sleep(3)

        # Next cursor
        next_cursor = str(start + len(items)) if len(items) == max_results else None

        return items, next_cursor
