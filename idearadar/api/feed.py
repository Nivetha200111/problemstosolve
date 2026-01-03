"""API endpoint: /api/feed - Get ranked feed of items."""
from flask import Flask, request, jsonify
from sqlalchemy import desc, and_, or_
from core.database import get_db
from core.models import Item
from api.utils import serialize_item, paginated_response, error_response

app = Flask(__name__)


@app.route("/api/feed", methods=["GET"])
def get_feed():
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
        sort = request.args.get("sort", "unique")
        topic = request.args.get("topic")
        source_id = request.args.get("source")
        page = int(request.args.get("page", 1))
        page_size = min(int(request.args.get("page_size", 20)), 100)

        if page < 1:
            return error_response("Page must be >= 1", 400)

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

            return jsonify(response), 200

    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        print(f"Error in /api/feed: {e}")
        return error_response("Internal server error", 500)


# Vercel serverless function handler
def handler(request):
    """Vercel handler."""
    with app.request_context(request.environ):
        return app.full_dispatch_request()
