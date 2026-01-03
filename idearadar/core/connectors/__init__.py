"""Connector factory."""
from typing import Dict, Any
from .base import BaseConnector, RawItem
from .rss import RSSConnector
from .hackernews import HackerNewsConnector
from .arxiv import ArxivConnector


def get_connector(connector_type: str, config: Dict[str, Any]) -> BaseConnector:
    """Factory function to get connector by type."""
    connectors = {
        "rss": RSSConnector,
        "hackernews": HackerNewsConnector,
        "arxiv": ArxivConnector,
    }

    connector_class = connectors.get(config.get("connector", connector_type))
    if not connector_class:
        raise ValueError(f"Unknown connector type: {connector_type}")

    return connector_class(config)


__all__ = ["BaseConnector", "RawItem", "get_connector"]
