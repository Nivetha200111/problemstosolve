"""API endpoint: /api/item - Get single item by ID."""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from core.database import get_db
from core.models import Item
from api.utils import serialize_item, error_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Get item by ID.

        Query params:
        - id: item ID (required)
        """
        try:
            # Parse query params
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            item_id = params.get("id", [None])[0]

            if not item_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_response("Missing 'id' parameter", 400)).encode())
                return

            try:
                item_id = int(item_id)
            except ValueError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_response("Invalid 'id' parameter", 400)).encode())
                return

            with get_db() as db:
                item = db.query(Item).filter_by(id=item_id).first()

                if not item:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(error_response("Item not found", 404)).encode())
                    return

                # Add "why unique" explanation
                response = serialize_item(item)

                # Generate "why unique" explanation
                why_unique = []

                if item.novelty_score > 0.7:
                    why_unique.append("High content novelty compared to recent items")
                elif item.novelty_score > 0.4:
                    why_unique.append("Moderate content novelty")
                else:
                    why_unique.append("Similar to existing content")

                if item.quality_score > 0.7:
                    why_unique.append("High quality signals (source, engagement, content)")

                if item.raw_signals_json:
                    score = item.raw_signals_json.get("score", 0)
                    if score > 100:
                        why_unique.append(f"High engagement: {score} points")

                    comments = item.raw_signals_json.get("descendants", 0)
                    if comments > 50:
                        why_unique.append(f"Active discussion: {comments} comments")

                response["why_unique"] = why_unique

                # If duplicate, include original
                if item.duplicate_of_item_id:
                    original = db.query(Item).filter_by(id=item.duplicate_of_item_id).first()
                    if original:
                        response["duplicate_of"] = {
                            "id": original.id,
                            "title": original.title,
                            "url": original.canonical_url
                        }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, default=str).encode())

        except Exception as e:
            print(f"Error in /api/item: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response("Internal server error", 500)).encode())
