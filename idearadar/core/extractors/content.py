"""Content extraction from URLs."""
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import trafilatura
from bs4 import BeautifulSoup
import hashlib
from core.config import settings


class ContentExtractor:
    """Extract clean content from web pages."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "IdeaRadar/1.0 (Research Tool; +https://github.com/yourorg/idearadar)"
        })

    def extract(self, url: str) -> Dict[str, Any]:
        """
        Extract content from URL.

        Returns dict with:
        - extracted_text: Clean main content
        - snippet: First ~300 chars
        - summary: Generated summary
        - domain: Domain name
        - language: Detected language
        - content_hash: Hash of extracted text
        """
        try:
            # Fetch URL with timeout
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()

            html = response.text

            # Extract with trafilatura
            extracted_text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False,
                no_fallback=False
            )

            if not extracted_text:
                # Fallback to BeautifulSoup
                extracted_text = self._fallback_extract(html)

            # Truncate to max length
            if extracted_text:
                extracted_text = extracted_text[:settings.content_max_length]

            # Generate snippet
            snippet = self._generate_snippet(extracted_text) if extracted_text else None

            # Generate summary
            summary = self._generate_summary(extracted_text) if extracted_text else None

            # Get domain
            domain = urlparse(url).netloc

            # Detect language (simple heuristic)
            language = self._detect_language(extracted_text) if extracted_text else None

            # Compute content hash
            content_hash = self._hash_content(extracted_text) if extracted_text else None

            return {
                "extracted_text": extracted_text,
                "snippet": snippet,
                "summary": summary,
                "domain": domain,
                "language": language,
                "content_hash": content_hash
            }

        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return {
                "extracted_text": None,
                "snippet": None,
                "summary": None,
                "domain": urlparse(url).netloc,
                "language": None,
                "content_hash": None
            }

    def _fallback_extract(self, html: str) -> Optional[str]:
        """Fallback extraction using BeautifulSoup."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            print(f"Fallback extraction failed: {e}")
            return None

    def _generate_snippet(self, text: str) -> str:
        """Generate snippet (first ~300 chars)."""
        if not text:
            return ""

        # Take first 300 chars at word boundary
        snippet = text[:300]
        last_space = snippet.rfind(" ")
        if last_space > 0:
            snippet = snippet[:last_space]

        return snippet.strip() + ("..." if len(text) > 300 else "")

    def _generate_summary(self, text: str) -> str:
        """
        Generate summary (simple heuristic).

        For MVP: First paragraph or first 3 sentences.
        Can be replaced with LLM-based summarization later.
        """
        if not text:
            return ""

        # Try first paragraph
        paragraphs = text.split("\n\n")
        if paragraphs:
            first_para = paragraphs[0].strip()
            if len(first_para) > 50 and len(first_para) < 500:
                return first_para

        # Fallback: first 3 sentences
        sentences = text.split(". ")
        summary = ". ".join(sentences[:3])
        if len(summary) > 500:
            summary = summary[:500]

        return summary.strip()

    def _detect_language(self, text: str) -> str:
        """Simple language detection (always returns 'en' for MVP)."""
        # For MVP, assume English. Can add langdetect library later.
        return "en"

    def _hash_content(self, text: str) -> str:
        """Hash content for deduplication."""
        if not text:
            return ""

        # Normalize text
        normalized = " ".join(text.lower().split())

        # SHA-256 hash
        return hashlib.sha256(normalized.encode()).hexdigest()
