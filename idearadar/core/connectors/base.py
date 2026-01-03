"""Base connector interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawItem:
    """Raw item from connector before processing."""
    title: str
    url: str
    published_at: Optional[datetime]
    author: Optional[str]
    source: str
    snippet: Optional[str]
    raw_data: Optional[Dict[str, Any]] = None  # Extra metadata


class BaseConnector(ABC):
    """Base class for content connectors."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize connector with config."""
        self.config = config

    @abstractmethod
    def fetch(self, cursor: Optional[str] = None, limit: int = 50) -> tuple[List[RawItem], Optional[str]]:
        """
        Fetch items from source.

        Args:
            cursor: Pagination cursor (format depends on connector)
            limit: Max items to fetch

        Returns:
            (items, next_cursor) tuple
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get connector name."""
        pass
