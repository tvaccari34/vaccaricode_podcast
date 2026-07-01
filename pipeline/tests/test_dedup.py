"""Tests for dedup key normalization."""

from __future__ import annotations

from boosternews.dedup import dedup_key, normalize_title


def test_normalize_strips_case_punctuation_accents():
    assert normalize_title("Rust's New Release!") == "rust release"
    assert normalize_title("SÃO PAULO devs") == "sao paulo devs"


def test_same_story_different_phrasing_collapses():
    a = dedup_key("The New Rust 2.0 Release is Here")
    b = dedup_key("Rust 2.0 release, now here")
    assert a == b


def test_different_stories_have_different_keys():
    assert dedup_key("Python 3.13 released") != dedup_key("Go 1.24 released")


def test_key_is_stable_hex():
    k = dedup_key("Anything")
    assert len(k) == 40 and all(c in "0123456789abcdef" for c in k)
