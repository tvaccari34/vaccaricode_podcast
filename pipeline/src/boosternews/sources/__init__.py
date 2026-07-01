"""Trend sources: fetchers that turn a configured source into candidate items."""

from .registry import get_fetcher, KNOWN_KINDS

__all__ = ["get_fetcher", "KNOWN_KINDS"]
