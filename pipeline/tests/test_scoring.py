"""Tests for relevance scoring."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from boosternews.models import SourceItem
from boosternews.scoring import (
    corroboration_multiplier,
    engagement_factor,
    recency_factor,
    score_item,
    topic_score,
)

NOW = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)


def test_recency_decays_with_age():
    fresh = recency_factor(NOW, now=NOW)
    half_life_old = recency_factor(NOW - timedelta(hours=48), now=NOW)
    older = recency_factor(NOW - timedelta(hours=96), now=NOW)
    assert fresh == 1.0
    assert round(half_life_old, 3) == 0.5
    assert older < half_life_old


def test_recency_unknown_is_neutral():
    assert recency_factor(None, now=NOW) == 0.5


def test_engagement_monotonic_and_log_scaled():
    assert engagement_factor(0) == 0.0
    assert engagement_factor(10) < engagement_factor(100) < engagement_factor(1000)
    assert round(engagement_factor(999), 1) == 1.0


def test_score_item_uses_source_weight():
    item = SourceItem(title="t", url="u", engagement=100, published_at=NOW)
    base = score_item(item, source_weight=1.0, now=NOW)
    weighted = score_item(item, source_weight=2.0, now=NOW)
    # score_item rounds to 4 dp, so allow a small tolerance on the doubling relationship.
    assert weighted == pytest.approx(2 * base, abs=1e-3)


def test_corroboration_increases_score():
    assert corroboration_multiplier(1) == 1.0
    assert corroboration_multiplier(3) > corroboration_multiplier(1)
    assert topic_score(0.5, 3) > topic_score(0.5, 1)
