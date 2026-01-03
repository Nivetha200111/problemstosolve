"""SimHash-based deduplication."""
from simhash import Simhash
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlunparse


def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL by removing tracking parameters and normalizing.

    Removes common tracking params like utm_*, fbclid, etc.
    """
    parsed = urlparse(url)

    # Remove tracking parameters
    tracking_params = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "ref", "source", "campaign_id", "_hsenc", "_hsmi"
    }

    # Parse query string
    query_params = parse_qs(parsed.query)

    # Filter out tracking params
    filtered_params = {
        k: v for k, v in query_params.items()
        if k not in tracking_params
    }

    # Rebuild query string
    new_query = "&".join(f"{k}={v[0]}" for k, v in filtered_params.items())

    # Rebuild URL
    canonical = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/") or "/",
        parsed.params,
        new_query,
        ""  # Remove fragment
    ))

    return canonical


def compute_simhash(text: str) -> int:
    """
    Compute SimHash for text.

    Returns 64-bit signed integer hash (compatible with PostgreSQL BIGINT).
    """
    if not text:
        return 0

    # Normalize text
    normalized = " ".join(text.lower().split())

    # Compute SimHash (unsigned 64-bit)
    hash_value = Simhash(normalized).value

    # Convert unsigned 64-bit to signed 64-bit for PostgreSQL BIGINT
    # If hash_value > 2^63-1, convert to negative representation
    if hash_value >= 2**63:
        hash_value = hash_value - 2**64

    return hash_value


def hamming_distance(hash1: int, hash2: int) -> int:
    """Compute Hamming distance between two hashes (handles signed integers)."""
    # Convert back to unsigned for XOR operation to work correctly
    if hash1 < 0:
        hash1 = hash1 + 2**64
    if hash2 < 0:
        hash2 = hash2 + 2**64

    xor = hash1 ^ hash2
    distance = bin(xor).count("1")
    return distance


def are_duplicates(hash1: int, hash2: int, threshold: int = 5) -> bool:
    """
    Check if two hashes represent duplicate content.

    Default threshold of 5 means up to 5 bits can differ.
    """
    return hamming_distance(hash1, hash2) <= threshold
