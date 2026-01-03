"""API endpoint: /api/item - Get single item by ID."""
from flask import Flask, request, jsonify
from core.database import get_db
from core.models import Item
from api.utils import serialize_item, error_response

app = Flask(__name__)


@app.route("/api/item", methods=["GET"])
def get_item():
    """
    Get item by ID.

    Query params:
    - id: item ID (required)
    """
    try:
        item_id = request.args.get("id")

        if not item_id:
            return error_response("Missing 'id' parameter", 400)

        try:
            item_id = int(item_id)
        except ValueError:
            return error_response("Invalid 'id' parameter", 400)

        with get_db() as db:
            item = db.query(Item).filter_by(id=item_id).first()

            if not item:
                return error_response("Item not found", 404)

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

            return jsonify(response), 200

    except Exception as e:
        print(f"Error in /api/item: {e}")
        return error_response("Internal server error", 500)


# Vercel serverless function handler
def handler(request):
    """Vercel handler."""
    with app.request_context(request.environ):
        return app.full_dispatch_request()
