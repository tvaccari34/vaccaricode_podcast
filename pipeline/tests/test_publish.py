"""Tests for publishing helpers (pure)."""

from __future__ import annotations

from boosternews.listmonk import build_campaign_payload, is_configured


def test_campaign_payload_shape():
    p = build_campaign_payload("My Edition", "My Subject", "**hi**", [3])
    assert p["name"] == "My Edition"
    assert p["subject"] == "My Subject"
    assert p["lists"] == [3]
    assert p["type"] == "regular"
    assert p["content_type"] == "markdown"
    assert p["body"] == "**hi**"


def test_not_configured_by_default():
    # conftest provides only the required secrets; Listmonk API creds are absent → unconfigured.
    assert is_configured() is False
