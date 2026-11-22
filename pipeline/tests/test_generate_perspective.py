"""Perspective/attribution rule and the author profile (pure: no network/DB)."""

from __future__ import annotations

import logging

import pytest

from boosternews import generate as gen_mod
from boosternews.config import get_settings
from boosternews.generate import (
    MAX_PROFILE_CHARS,
    author_profile,
    build_prompt,
    source_block,
    source_publishers,
    system_instruction,
)

TOPIC = {
    "id": "t-1",
    "title": "How we cut our cloud bill by 40%",
    "summary": "A team's cost story.",
    "urls": [
        "https://www.example.com/blog/cloud-bill",
        "https://news.ycombinator.com/item?id=1",
        "https://example.com/other",
    ],
    "extracted_text": "We migrated our stack last year and I was surprised by the savings.",
}


@pytest.fixture
def no_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTHOR_PROFILE_FILE", str(tmp_path / "missing.md"))
    monkeypatch.delenv("AUTHOR_PROFILE", raising=False)
    get_settings.cache_clear()


@pytest.mark.parametrize("fmt", ["blog", "podcast", "newsletter"])
def test_every_format_prompt_has_perspective_rule(fmt):
    p = build_prompt(TOPIC, fmt)
    assert "PERSPECTIVE AND ATTRIBUTION" in p
    assert "third person" in p
    assert "Tiago Vaccari" in p  # rule names the host
    assert "{author}" not in p  # fully formatted


def test_perspective_rule_survives_brand_voice_override(monkeypatch):
    monkeypatch.setenv("BRAND_VOICE", "Custom voice, nothing else.")
    get_settings.cache_clear()
    assert "PERSPECTIVE AND ATTRIBUTION" in build_prompt(TOPIC, "podcast")


def test_source_publishers_unique_without_www_in_order():
    assert source_publishers(TOPIC["urls"]) == ["example.com", "news.ycombinator.com"]
    assert source_publishers(["not a url", ""]) == []


def test_source_block_lists_publishers():
    assert "PUBLISHED BY: example.com, news.ycombinator.com" in source_block(TOPIC)
    assert "PUBLISHED BY" not in source_block({**TOPIC, "urls": []})


def test_no_profile_configured(no_profile):
    assert author_profile() == ""
    system = system_instruction()
    assert "AUTHOR PROFILE" not in system
    assert system == gen_mod.brand_voice()


def test_profile_from_file_wins_over_env_and_is_reread(monkeypatch, tmp_path):
    f = tmp_path / "author_profile.md"
    f.write_text("- 20+ years building software\n", encoding="utf-8")
    monkeypatch.setenv("AUTHOR_PROFILE_FILE", str(f))
    monkeypatch.setenv("AUTHOR_PROFILE", "env text")
    get_settings.cache_clear()
    assert author_profile() == "- 20+ years building software"

    f.write_text("- edited profile\n", encoding="utf-8")  # no restart, no cache clear
    assert author_profile() == "- edited profile"
    system = system_instruction()
    assert "=== AUTHOR PROFILE ===\n- edited profile\n=== END AUTHOR PROFILE ===" in system
    assert "ONLY allowed source" in system


def test_empty_file_falls_back_to_env_text(monkeypatch, tmp_path):
    f = tmp_path / "author_profile.md"
    f.write_text("  \n", encoding="utf-8")
    monkeypatch.setenv("AUTHOR_PROFILE_FILE", str(f))
    monkeypatch.setenv("AUTHOR_PROFILE", "  inline profile  ")
    get_settings.cache_clear()
    assert author_profile() == "inline profile"


def test_oversized_profile_is_truncated_with_warning(monkeypatch, tmp_path, caplog):
    f = tmp_path / "author_profile.md"
    f.write_text("x" * (MAX_PROFILE_CHARS + 500), encoding="utf-8")
    monkeypatch.setenv("AUTHOR_PROFILE_FILE", str(f))
    get_settings.cache_clear()
    with caplog.at_level(logging.WARNING, logger="boosternews.generate"):
        assert len(author_profile()) == MAX_PROFILE_CHARS
    assert "truncating" in caplog.text


def test_generate_for_topic_uses_profile_in_system(monkeypatch, tmp_path):
    """The orchestrator passes system_instruction() (brand voice + profile) to every format call."""
    f = tmp_path / "author_profile.md"
    f.write_text("- moved from the UK to Orlando in 2023", encoding="utf-8")
    monkeypatch.setenv("AUTHOR_PROFILE_FILE", str(f))
    monkeypatch.setenv("SECONDARY_LANGUAGE", "")
    get_settings.cache_clear()

    systems: list[str | None] = []

    def fake_gen(prompt, system=None, **_kw):
        systems.append(system)
        return "Generated text."

    class _Conn:
        def commit(self):
            pass

    class _Ctx:
        def __enter__(self):
            return _Conn()

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(gen_mod.repo, "get_topic", lambda tid: {**TOPIC, "id": tid})
    monkeypatch.setattr(gen_mod, "get_conn", lambda *a, **k: _Ctx())
    monkeypatch.setattr(gen_mod.repo, "upsert_draft", lambda *a, **k: "d")
    monkeypatch.setattr(gen_mod.repo, "upsert_episode", lambda *a, **k: "e")
    monkeypatch.setattr(gen_mod.repo, "set_topic_status", lambda *a, **k: None)

    gen_mod.generate_for_topic("t-1", gen=fake_gen)
    format_calls = [s for s in systems if s is not None]
    assert len(format_calls) == 3
    assert all("moved from the UK to Orlando in 2023" in s for s in format_calls)
