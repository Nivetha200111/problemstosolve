"""API endpoint: /api/search - Search items."""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from sqlalchemy import desc, or_, and_
from core.database import get_db
from core.models import Item
from api.utils import serialize_item, paginated_response, error_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Search items.

        Query params:
        - q: search query (required)
        - sort: unique|relevance (default: relevance)
        - page: page number (default: 1)
        - page_size: items per page (default: 20, max: 100)
        """
        try:
            # Parse query params
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            query_string = params.get("q", [""])[0].strip()
            sort = params.get("sort", ["relevance"])[0]
            page = int(params.get("page", [1])[0])
            page_size = min(int(params.get("page_size", [20])[0]), 100)

            if not query_string:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_response("Missing 'q' parameter", 400)).encode())
                return

            if page < 1:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_response("Page must be >= 1", 400)).encode())
                return

            with get_db() as db:
                # Build search query
                # Search in title, snippet, summary
                search_filter = or_(
                    Item.title.ilike(f"%{query_string}%"),
                    Item.snippet.ilike(f"%{query_string}%"),
                    Item.summary.ilike(f"%{query_string}%")
                )

                query = db.query(Item).filter(
                    and_(
                        search_filter,
                        Item.duplicate_of_item_id.is_(None)  # Exclude duplicates
                    )
                )

                # Apply sorting
                if sort == "unique":
                    query = query.order_by(desc(Item.novelty_score), desc(Item.published_at))
                else:  # relevance (simple: by final_score + recency)
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
            print(f"Error in /api/search: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response("Internal server error", 500)).encode())
