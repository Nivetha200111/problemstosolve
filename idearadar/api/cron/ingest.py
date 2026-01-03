"""API endpoint: /api/cron/ingest - Scheduled ingestion."""
from flask import Flask, request, jsonify
from core.database import get_db
from core.ingestion import IngestionPipeline
from core.config import settings
from api.utils import error_response

app = Flask(__name__)


@app.route("/api/cron/ingest", methods=["GET", "POST"])
def cron_ingest():
    """
    Scheduled ingestion endpoint.

    Protected by CRON_SECRET in header or query param.
    """
    try:
        # Authenticate
        auth_header = request.headers.get("X-Cron-Secret")
        auth_query = request.args.get("secret")

        provided_secret = auth_header or auth_query

        if not provided_secret or provided_secret != settings.cron_secret:
            return error_response("Unauthorized", 401)

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

        return jsonify(response), 200

    except Exception as e:
        print(f"Error in /api/cron/ingest: {e}")
        return error_response(f"Internal server error: {str(e)}", 500)


# Vercel serverless function handler
def handler(request):
    """Vercel handler."""
    with app.request_context(request.environ):
        return app.full_dispatch_request()
