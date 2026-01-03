"""Deduplication utilities."""
from .simhash import (
    canonicalize_url,
    compute_simhash,
    hamming_distance,
    are_duplicates
)

__all__ = [
    "canonicalize_url",
    "compute_simhash",
    "hamming_distance",
    "are_duplicates"
]
