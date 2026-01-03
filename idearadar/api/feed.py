"""API endpoint: /api/feed - Get ranked feed of items."""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from sqlalchemy import desc, or_
from core.database import get_db
from core.models import Item
from api.utils import serialize_item, paginated_response, error_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Get ranked feed of items.

        Query params:
        - sort: unique|top|new (default: unique)
        - topic: filter by domain or keyword
        - source: filter by source_id
        - page: page number (default: 1)
        - page_size: items per page (default: 20, max: 100)
        """
        try:
            # Parse query params
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            sort = params.get("sort", ["unique"])[0]
            topic = params.get("topic", [None])[0]
            source_id = params.get("source", [None])[0]
            page = int(params.get("page", [1])[0])
            page_size = min(int(params.get("page_size", [20])[0]), 100)

            if page < 1:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_response("Page must be >= 1", 400)).encode())
                return

            with get_db() as db:
                # Build query
                query = db.query(Item).filter(
                    Item.duplicate_of_item_id.is_(None)  # Exclude duplicates
                )

                # Apply filters
                if source_id:
                    query = query.filter(Item.source_id == int(source_id))

                if topic:
                    # Search in title, snippet, or domain
                    search_filter = or_(
                        Item.title.ilike(f"%{topic}%"),
                        Item.snippet.ilike(f"%{topic}%"),
                        Item.domain.ilike(f"%{topic}%")
                    )
                    query = query.filter(search_filter)

                # Apply sorting
                if sort == "unique":
                    query = query.order_by(desc(Item.novelty_score), desc(Item.published_at))
                elif sort == "top":
                    query = query.order_by(desc(Item.final_score), desc(Item.published_at))
                elif sort == "new":
                    query = query.order_by(desc(Item.published_at))
                else:
                    query = query.order_by(desc(Item.final_score), desc(Item.published_at))

                # Get total count
                total = query.count()

                # Paginate
                offset = (page - 1) * page_size
                items = query.offset(offset).limit(page_size).all()

                # Serialize
                serialized = [serialize_item(item) for item in items]

                # Return paginated response
                response = paginated_response(serialized, total, page, page_size)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, default=str).encode())

        except ValueError as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response(f"Invalid parameter: {str(e)}", 400)).encode())
        except Exception as e:
            print(f"Error in /api/feed: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response("Internal server error", 500)).encode())
