"""Shared dataclasses for the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class SourceRow:
    """A configured trend source, as stored in the ``sources`` table."""

    id: str
    name: str
    kind: str
    url: str | None
    config: dict
    enabled: bool
    fetch_interval_minutes: int
    last_fetched_at: datetime | None = None


@dataclass(slots=True)
class SourceItem:
    """A single candidate item fetched from a source, before dedup/persistence."""

    title: str
    url: str
    external_id: str | None = None
    summary: str | None = None
    published_at: datetime | None = None
    engagement: int = 0  # HN points / GitHub stars / 0 when unknown
    extra: dict = field(default_factory=dict)
