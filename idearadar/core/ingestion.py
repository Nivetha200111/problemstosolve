"""Ingestion pipeline."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from core.models import Source, Item
from core.connectors import get_connector, RawItem
from core.extractors import ContentExtractor
from core.dedup import canonicalize_url, compute_simhash, are_duplicates
from core.scoring import ScoringEngine
from core.config import settings
import json


class IngestionPipeline:
    """Orchestrate content ingestion from sources."""

    def __init__(self, db: Session):
        self.db = db
        self.extractor = ContentExtractor()
        self.scorer = ScoringEngine(db)

    def ingest_source(
        self,
        source: Source,
        max_items: int = 50
    ) -> Dict[str, Any]:
        """
        Ingest items from a single source.

        Returns statistics: processed, inserted, deduped, errors.
        """
        stats = {
            "source_id": source.id,
            "source_name": source.name,
            "processed": 0,
            "inserted": 0,
            "deduped": 0,
            "errors": []
        }

        try:
            # Get connector
            connector = get_connector(source.type, source.config_json)

            # Get cursor from last run (stored in config_json)
            cursor = source.config_json.get("cursor")

            # Fetch items
            raw_items, next_cursor = connector.fetch(cursor=cursor, limit=max_items)

            stats["processed"] = len(raw_items)

            # Process each item
            for raw_item in raw_items:
                try:
                    self._process_item(raw_item, source, stats)
                except Exception as e:
                    error_msg = f"Error processing item {raw_item.url}: {str(e)}"
                    print(error_msg)
                    stats["errors"].append(error_msg)

            # Update source cursor and last_run
            source.config_json["cursor"] = next_cursor
            source.last_run_at = datetime.utcnow()

            self.db.commit()

        except Exception as e:
            error_msg = f"Error ingesting source {source.name}: {str(e)}"
            print(error_msg)
            stats["errors"].append(error_msg)
            self.db.rollback()

        return stats

    def _process_item(
        self,
        raw_item: RawItem,
        source: Source,
        stats: Dict[str, Any]
    ) -> Optional[Item]:
        """Process a single raw item through the pipeline."""

        # 1. Canonicalize URL
        canonical_url = canonicalize_url(raw_item.url)

        # 2. Check if URL already exists
        existing = self.db.query(Item).filter_by(canonical_url=canonical_url).first()
        if existing:
            stats["deduped"] += 1
            return None

        # 3. Extract content (if we don't have snippet from connector)
        extracted_text = None
        snippet = raw_item.snippet
        summary = None
        domain = None
        content_hash = None

        if not snippet or len(snippet) < 100:
            # Extract from URL
            extraction = self.extractor.extract(raw_item.url)
            extracted_text = extraction.get("extracted_text")
            snippet = extraction.get("snippet") or snippet
            summary = extraction.get("summary")
            domain = extraction.get("domain")
            content_hash = extraction.get("content_hash")
        else:
            # Use snippet from connector
            from urllib.parse import urlparse
            domain = urlparse(raw_item.url).netloc
            summary = snippet  # Use snippet as summary for now

        # 4. Compute SimHash
        text_for_hash = extracted_text or snippet or raw_item.title
        simhash = compute_simhash(text_for_hash) if text_for_hash else None

        # 5. Check for near-duplicates
        if simhash:
            duplicate_of = self._find_duplicate(simhash)
            if duplicate_of:
                stats["deduped"] += 1
                # Still create item but mark as duplicate
                duplicate_of_id = duplicate_of.id
            else:
                duplicate_of_id = None
        else:
            duplicate_of_id = None

        # 6. Score item
        scores = self.scorer.score_item(
            simhash=simhash or 0,
            published_at=raw_item.published_at,
            raw_signals=raw_item.raw_data,
            source_id=source.id,
            extracted_text=extracted_text,
            domain=domain
        )

        # 7. Create item
        item = Item(
            canonical_url=canonical_url,
            title=raw_item.title,
            source_id=source.id,
            published_at=raw_item.published_at,
            snippet=snippet[:1000] if snippet else None,  # Truncate
            summary=summary[:2000] if summary else None,  # Truncate
            domain=domain,
            content_hash=content_hash,
            simhash=simhash,
            duplicate_of_item_id=duplicate_of_id,
            novelty_score=scores["novelty_score"],
            quality_score=scores["quality_score"],
            final_score=scores["final_score"],
            raw_signals_json=raw_item.raw_data
        )

        self.db.add(item)

        # Don't count duplicates in inserted count
        if not duplicate_of_id:
            stats["inserted"] += 1

        return item

    def _find_duplicate(self, simhash: int) -> Optional[Item]:
        """Find duplicate item by SimHash."""

        # Get recent items with simhash
        candidates = self.db.query(Item).filter(
            Item.simhash.isnot(None),
            Item.duplicate_of_item_id.is_(None)  # Only check against non-duplicates
        ).order_by(Item.created_at.desc()).limit(500).all()

        for candidate in candidates:
            if are_duplicates(simhash, candidate.simhash, settings.simhash_threshold):
                return candidate

        return None

    def ingest_all_sources(self, max_items_per_source: int = 50) -> List[Dict[str, Any]]:
        """
        Ingest from all enabled sources.

        Returns list of statistics per source.
        """
        sources = self.db.query(Source).filter_by(enabled=True).all()

        all_stats = []

        for source in sources:
            print(f"Ingesting source: {source.name}")
            stats = self.ingest_source(source, max_items=max_items_per_source)
            all_stats.append(stats)
            print(f"  Processed: {stats['processed']}, Inserted: {stats['inserted']}, Deduped: {stats['deduped']}")

        return all_stats
