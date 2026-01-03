"""Scoring engine for content ranking."""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.models import Item
from core.config import settings
from core.dedup import hamming_distance


class ScoringEngine:
    """Compute novelty, quality, and final scores for items."""

    def __init__(self, db: Session):
        self.db = db
        self.novelty_weight = settings.novelty_weight
        self.quality_weight = settings.quality_weight
        self.recency_weight = settings.recency_weight

    def compute_novelty_score(
        self,
        simhash: int,
        embedding: Optional[list] = None,
        domain: Optional[str] = None
    ) -> float:
        """
        Compute novelty score based on similarity to existing items.

        Returns score between 0 (duplicate) and 1 (very novel).
        """
        if not simhash:
            return 0.5  # Default for items without hash

        # Find similar items using SimHash
        # Get recent items (last 30 days) to compare against
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        recent_items = self.db.query(Item.simhash).filter(
            Item.simhash.isnot(None),
            Item.created_at >= cutoff_date
        ).limit(1000).all()

        if not recent_items:
            return 1.0  # Very novel if no existing items

        # Compute minimum Hamming distance to existing items
        min_distance = 64  # Max possible for 64-bit hash

        for (existing_hash,) in recent_items:
            if existing_hash:
                distance = hamming_distance(simhash, existing_hash)
                min_distance = min(min_distance, distance)

        # Normalize to 0-1 score
        # Distance 0 = duplicate (score 0)
        # Distance >= 32 = very different (score 1)
        novelty = min(min_distance / 32.0, 1.0)

        return novelty

    def compute_quality_score(
        self,
        raw_signals: Optional[Dict[str, Any]] = None,
        source_id: Optional[int] = None,
        extracted_text: Optional[str] = None
    ) -> float:
        """
        Compute quality score based on various signals.

        Returns score between 0 and 1.
        """
        score = 0.0
        factors = 0

        # Source weight (different sources have different quality)
        source_weights = {
            1: 0.8,  # HN Top Stories - high quality
            2: 0.9,  # arXiv CS.AI - very high quality
            3: 0.9,  # arXiv CS.LG - very high quality
            4: 0.6,  # TechCrunch - medium quality
            5: 0.7,  # MIT News - high quality
            6: 0.6,  # Product Hunt - medium quality
        }

        if source_id in source_weights:
            score += source_weights[source_id]
            factors += 1
        else:
            score += 0.5  # Default source quality
            factors += 1

        # Engagement signals (HN points, comments)
        if raw_signals:
            hn_score = raw_signals.get("score", 0)
            if hn_score > 0:
                # Normalize HN score (100+ points = high quality)
                engagement_score = min(hn_score / 100.0, 1.0)
                score += engagement_score
                factors += 1

            comments = raw_signals.get("descendants", 0)
            if comments > 0:
                # Normalize comment count (50+ comments = high engagement)
                comment_score = min(comments / 50.0, 1.0)
                score += comment_score
                factors += 1

        # Content quality heuristics
        if extracted_text:
            text_len = len(extracted_text)

            # Length score (500-5000 chars is good)
            if text_len >= 500 and text_len <= 5000:
                score += 0.8
                factors += 1
            elif text_len > 5000:
                score += 0.6
                factors += 1
            else:
                score += 0.3
                factors += 1

            # Check for code blocks (indicates technical content)
            if "```" in extracted_text or "def " in extracted_text or "function " in extracted_text:
                score += 0.7
                factors += 1

        # Average all factors
        return score / factors if factors > 0 else 0.5

    def compute_recency_score(self, published_at: Optional[datetime]) -> float:
        """
        Compute recency score with exponential decay.

        Returns score between 0 and 1.
        """
        if not published_at:
            return 0.5  # Default for unknown dates

        now = datetime.utcnow()

        # Make published_at timezone-naive if needed
        if published_at.tzinfo is not None:
            published_at = published_at.replace(tzinfo=None)

        age_hours = (now - published_at).total_seconds() / 3600

        if age_hours < 0:
            return 1.0  # Future date (edge case)

        # Exponential decay
        # Half-life of 24 hours
        half_life = 24
        decay_factor = 0.5 ** (age_hours / half_life)

        return max(min(decay_factor, 1.0), 0.0)

    def compute_final_score(
        self,
        novelty_score: float,
        quality_score: float,
        recency_score: float
    ) -> float:
        """
        Compute final weighted score.

        Returns score between 0 and 1.
        """
        final = (
            self.novelty_weight * novelty_score +
            self.quality_weight * quality_score +
            self.recency_weight * recency_score
        )

        return max(min(final, 1.0), 0.0)

    def score_item(
        self,
        simhash: int,
        published_at: Optional[datetime],
        raw_signals: Optional[Dict[str, Any]],
        source_id: int,
        extracted_text: Optional[str],
        domain: Optional[str]
    ) -> Dict[str, float]:
        """
        Score an item and return all scores.

        Returns dict with novelty_score, quality_score, recency_score, final_score.
        """
        novelty = self.compute_novelty_score(simhash, domain=domain)
        quality = self.compute_quality_score(raw_signals, source_id, extracted_text)
        recency = self.compute_recency_score(published_at)
        final = self.compute_final_score(novelty, quality, recency)

        return {
            "novelty_score": novelty,
            "quality_score": quality,
            "recency_score": recency,
            "final_score": final
        }
