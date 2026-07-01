"""Maps a source ``kind`` to its fetcher."""

from __future__ import annotations

from collections.abc import Callable

from ..models import SourceItem, SourceRow
from .github import fetch_github_trending
from .hackernews import fetch_hackernews
from .rss import fetch_rss

Fetcher = Callable[[SourceRow], list[SourceItem]]

_FETCHERS: dict[str, Fetcher] = {
    "rss": fetch_rss,
    "atom": fetch_rss,
    "hackernews": fetch_hackernews,
    "github_trending": fetch_github_trending,
}

KNOWN_KINDS = tuple(_FETCHERS)


def get_fetcher(kind: str) -> Fetcher:
    try:
        return _FETCHERS[kind]
    except KeyError:
        raise ValueError(f"Unknown source kind '{kind}'. Known: {', '.join(KNOWN_KINDS)}") from None
