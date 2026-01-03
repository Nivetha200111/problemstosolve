"""Configuration management."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = os.getenv("DATABASE_URL", "")

    # Security
    cron_secret: str = os.getenv("CRON_SECRET", "change-me-in-production")

    # Scoring weights
    novelty_weight: float = float(os.getenv("NOVELTY_WEIGHT", "0.5"))
    quality_weight: float = float(os.getenv("QUALITY_WEIGHT", "0.35"))
    recency_weight: float = float(os.getenv("RECENCY_WEIGHT", "0.15"))

    # Ingestion
    max_items_per_cron: int = int(os.getenv("MAX_ITEMS_PER_CRON", "50"))
    content_max_length: int = int(os.getenv("CONTENT_MAX_LENGTH", "10000"))

    # Embeddings (optional)
    embedding_api_url: Optional[str] = os.getenv("EMBEDDING_API_URL")
    embedding_api_key: Optional[str] = os.getenv("EMBEDDING_API_KEY")

    # Rate limiting
    rate_limit_per_domain: int = int(os.getenv("RATE_LIMIT_PER_DOMAIN", "10"))

    # SimHash settings
    simhash_threshold: int = int(os.getenv("SIMHASH_THRESHOLD", "5"))  # Hamming distance

    # Vector similarity threshold (if using pgvector)
    vector_similarity_threshold: float = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "0.85"))

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
