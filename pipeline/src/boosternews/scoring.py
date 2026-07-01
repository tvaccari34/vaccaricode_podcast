"""Relevance scoring for candidate topics.

Score combines three explainable signals:
  - recency:      exponential decay with a configurable half-life (fresher = higher)
  - engagement:   log-scaled HN points / GitHub stars (popular = higher)
  - corroboration: a bonus when multiple distinct sources surface the same story

``base_score`` (recency + engagement, weighted by the source) is stored per topic; the final
``score`` multiplies it by a corroboration factor based on how many sources merged into it.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from .models import SourceItem

RECENCY_HALF_LIFE_HOURS = 48.0
RECENCY_WEIGHT = 0.6
ENGAGEMENT_WEIGHT = 0.4
CORROBORATION_PER_EXTRA_SOURCE = 0.25


def recency_factor(published_at: datetime | None, *, now: datetime | None = None) -> float:
    """1.0 for brand-new items, decaying by half every ``RECENCY_HALF_LIFE_HOURS``."""
    if published_at is None:
        return 0.5  # unknown age → neutral
    now = now or datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (now - published_at).total_seconds() / 3600.0)
    return 0.5 ** (age_hours / RECENCY_HALF_LIFE_HOURS)


def engagement_factor(engagement: int) -> float:
    """Log-scaled engagement: ~0 at 0, ~1.0 around 1000 points/stars."""
    return math.log10(max(0, engagement) + 1) / 3.0


def score_item(
    item: SourceItem, *, source_weight: float = 1.0, now: datetime | None = None
) -> float:
    """Base score for a single fetched item (before corroboration)."""
    base = RECENCY_WEIGHT * recency_factor(
        item.published_at, now=now
    ) + ENGAGEMENT_WEIGHT * engagement_factor(item.engagement)
    return round(source_weight * base, 4)


def corroboration_multiplier(num_sources: int) -> float:
    return 1.0 + CORROBORATION_PER_EXTRA_SOURCE * max(0, num_sources - 1)


def topic_score(base_score: float, num_sources: int) -> float:
    """Final topic score = base × corroboration multiplier."""
    return round(base_score * corroboration_multiplier(num_sources), 4)
