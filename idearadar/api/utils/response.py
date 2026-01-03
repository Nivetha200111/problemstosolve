"""API response utilities."""
from typing import Any, Dict, List, Optional
from datetime import datetime


def serialize_item(item) -> Dict[str, Any]:
    """Serialize Item model to JSON-compatible dict."""
    return {
        "id": item.id,
        "title": item.title,
        "url": item.canonical_url,
        "domain": item.domain,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "fetched_at": item.fetched_at.isoformat() if item.fetched_at else None,
        "snippet": item.snippet,
        "summary": item.summary,
        "source": {
            "id": item.source_id,
            "name": item.source.name if item.source else None
        },
        "scores": {
            "novelty": round(item.novelty_score, 3),
            "quality": round(item.quality_score, 3),
            "final": round(item.final_score, 3)
        },
        "signals": item.raw_signals_json,
        "is_duplicate": item.duplicate_of_item_id is not None
    }


def json_response(data: Any, status_code: int = 200) -> tuple[Dict[str, Any], int]:
    """Create JSON response tuple."""
    return data, status_code


def error_response(message: str, status_code: int = 400) -> tuple[Dict[str, Any], int]:
    """Create error response."""
    return {"error": message}, status_code


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int
) -> Dict[str, Any]:
    """Create paginated response."""
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
