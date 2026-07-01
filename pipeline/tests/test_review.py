"""Tests for review state transitions and the publish gate (pure logic)."""

from __future__ import annotations

import pytest

from boosternews.review import (
    PublishGateError,
    assert_publishable,
    decision_to_status,
)


def test_decision_maps_to_status():
    assert decision_to_status("approve") == "approved"
    assert decision_to_status("reject") == "rejected"
    assert decision_to_status("request_edit") == "needs_edit"


def test_unknown_decision_rejected():
    with pytest.raises(KeyError):
        decision_to_status("yolo")


@pytest.mark.parametrize("status", ["pending_review", "rejected", "needs_edit", "published"])
def test_publish_gate_blocks_unapproved(status):
    with pytest.raises(PublishGateError):
        assert_publishable(status)


def test_publish_gate_allows_approved():
    # Should not raise.
    assert_publishable("approved")
