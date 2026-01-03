"""API endpoint: /api/search - Search items."""
from flask import Flask, request, jsonify
from sqlalchemy import desc, or_, func
from core.database import get_db
from core.models import Item
from api.utils import serialize_item, paginated_response, error_response

app = Flask(__name__)


@app.route("/api/search", methods=["GET"])
def search_items():
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
        query_string = request.args.get("q", "").strip()
        sort = request.args.get("sort", "relevance")
        page = int(request.args.get("page", 1))
        page_size = min(int(request.args.get("page_size", 20)), 100)

        if not query_string:
            return error_response("Missing 'q' parameter", 400)

        if page < 1:
            return error_response("Page must be >= 1", 400)

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

            return jsonify(response), 200

    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        print(f"Error in /api/search: {e}")
        return error_response("Internal server error", 500)


# Vercel serverless function handler
def handler(request):
    """Vercel handler."""
    with app.request_context(request.environ):
        return app.full_dispatch_request()
