"""Database models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    JSON, ForeignKey, Index, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

Base = declarative_base()


class Source(Base):
    """Content source (RSS, API, scrape)."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # rss, api, scrape
    config_json = Column(JSON, nullable=False)  # connector-specific config
    enabled = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    items = relationship("Item", back_populates="source")


class Item(Base):
    """Discovered content item."""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_url = Column(String(2048), nullable=False, unique=True, index=True)
    title = Column(String(1024), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    fetched_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    snippet = Column(Text, nullable=True)  # First ~300 chars
    summary = Column(Text, nullable=True)  # Generated summary
    domain = Column(String(255), nullable=True, index=True)
    language = Column(String(10), nullable=True)

    # Deduplication
    content_hash = Column(String(64), nullable=True, index=True)
    simhash = Column(BigInteger, nullable=True, index=True)
    duplicate_of_item_id = Column(Integer, ForeignKey("items.id"), nullable=True, index=True)

    # Scoring
    novelty_score = Column(Float, default=0.0, nullable=False)
    quality_score = Column(Float, default=0.0, nullable=False)
    final_score = Column(Float, default=0.0, nullable=False, index=True)

    # Metadata
    raw_signals_json = Column(JSON, nullable=True)  # engagement, author, etc.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    source = relationship("Source", back_populates="items")

    __table_args__ = (
        Index("idx_items_score_published", "final_score", "published_at"),
        Index("idx_items_domain_score", "domain", "final_score"),
    )


# If pgvector is available, add embedding column
if HAS_PGVECTOR:
    Item.embedding = Column(Vector(384), nullable=True)  # 384-dim for sentence-transformers mini


class Collection(Base):
    """User collection (anonymous via token)."""
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_token = Column(String(255), nullable=False, index=True)  # client-generated UUID
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    saved_items = relationship("SavedItem", back_populates="collection")


class SavedItem(Base):
    """Items saved to collections."""
    __tablename__ = "saved_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    saved_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    collection = relationship("Collection", back_populates="saved_items")
    item = relationship("Item")

    __table_args__ = (
        Index("idx_saved_items_unique", "collection_id", "item_id", unique=True),
    )
