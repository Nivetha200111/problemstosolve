"""API endpoint: /api/cron/ingest - Scheduled ingestion."""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from core.database import get_db
from core.ingestion import IngestionPipeline
from core.config import settings
from api.utils import error_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def _handle_request(self):
        """
        Scheduled ingestion endpoint.

        Protected by CRON_SECRET in header or query param.
        """
        try:
            # Parse query params for secret
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            # Authenticate
            auth_header = self.headers.get("X-Cron-Secret")
            auth_query = params.get("secret", [None])[0]

            provided_secret = auth_header or auth_query

            if not provided_secret or provided_secret != settings.cron_secret:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_response("Unauthorized", 401)).encode())
                return

            # Run ingestion
            with get_db() as db:
                pipeline = IngestionPipeline(db)

                # Ingest from all sources with limit
                max_items = settings.max_items_per_cron
                all_stats = pipeline.ingest_all_sources(max_items_per_source=max_items)

            # Calculate totals
            total_processed = sum(s["processed"] for s in all_stats)
            total_inserted = sum(s["inserted"] for s in all_stats)
            total_deduped = sum(s["deduped"] for s in all_stats)
            total_errors = sum(len(s["errors"]) for s in all_stats)

            response = {
                "status": "success",
                "summary": {
                    "total_processed": total_processed,
                    "total_inserted": total_inserted,
                    "total_deduped": total_deduped,
                    "total_errors": total_errors
                },
                "sources": all_stats
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, default=str).encode())

        except Exception as e:
            print(f"Error in /api/cron/ingest: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response(f"Internal server error: {str(e)}", 500)).encode())
