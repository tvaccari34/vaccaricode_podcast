"""Tests for review state transitions and the publish gate (pure logic)."""

from __future__ import annotations

import pytest

from boosternews.review import (
    PublishGateError,
    assert_audio_present,
    assert_publishable,
    decision_to_status,
    episode_audio_ready,
    should_narrate_on_approval,
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


# ── Narration-on-approval policy ────────────────────────────────────────────
def _narrate(**kw):
    base = {
        "channel": "podcast",
        "decision": "approve",
        "language": "pt-BR",
        "primary_language": "pt-BR",
        "secondary_enabled": False,
    }
    return should_narrate_on_approval(**{**base, **kw})


def test_approving_primary_podcast_narrates():
    assert _narrate() is True


@pytest.mark.parametrize("decision", ["reject", "request_edit"])
def test_only_approval_narrates(decision):
    assert _narrate(decision=decision) is False


@pytest.mark.parametrize("channel", ["blog", "newsletter"])
def test_only_podcast_narrates(channel):
    assert _narrate(channel=channel) is False


def test_secondary_language_needs_the_flag():
    assert _narrate(language="en") is False
    assert _narrate(language="en", secondary_enabled=True) is True


def test_generation_no_longer_narrates():
    """Regression guard: generate must not queue narration (it burned the TTS quota on drafts)."""
    import inspect

    from boosternews import generate

    src = inspect.getsource(generate)
    assert "enqueue_narration" not in src


# ── Audio gate ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("url", [None, "", "   "])
def test_audio_gate_blocks_silent_episode(url):
    assert episode_audio_ready(url) is False
    with pytest.raises(PublishGateError):
        assert_audio_present(url)


def test_audio_gate_allows_narrated_episode():
    assert episode_audio_ready("https://example.com/a.mp3") is True
    assert_audio_present("https://example.com/a.mp3")  # should not raise
