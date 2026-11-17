"""Dashboard: secondary-language (English) narration controls follow NARRATION_SECONDARY_ENABLED."""

from __future__ import annotations

from contextlib import contextmanager

import pytest

from boosternews.config import get_settings
from boosternews.dashboard import app as dash

EN_REVIEW = {
    "id": "11111111-1111-1111-1111-111111111111",
    "language": "en",
    "title": "An English episode",
    "status": "approved",
    "audio_url": "https://example.test/audio/podcast/1111.mp3",
    "duration": 300,
    "script": "Hello and welcome.",
}
EN_PUBLISHED = {**EN_REVIEW, "id": "22222222-2222-2222-2222-222222222222", "status": "published"}


def _render_index(secondary_narration: bool) -> str:
    return dash._env.get_template("index.html").render(
        queue=[],
        reviewer="tester",
        primary="pt-BR",
        manual=[EN_REVIEW, EN_PUBLISHED],
        episodes=[],
        secondary_narration=secondary_narration,
    )


def test_english_episodes_get_renarrate_when_secondary_narration_enabled():
    html = _render_index(True)
    for ep in (EN_REVIEW, EN_PUBLISHED):
        assert f'action="/episode/{ep["id"]}/renarrate"' in html
        assert f'action="/episode/{ep["id"]}/audio"' in html  # manual upload stays available
    assert "Hello and welcome." in html  # script prefilled in the edit box
    assert "record &amp; upload" not in html


def test_english_episodes_upload_only_when_secondary_narration_disabled():
    html = _render_index(False)
    assert "/renarrate" not in html
    assert f'action="/episode/{EN_REVIEW["id"]}/audio"' in html
    assert "record &amp; upload" in html


@pytest.mark.parametrize("enabled", [True, False])
def test_create_episode_form_offers_secondary_narrate_only_when_enabled(enabled):
    html = dash._env.get_template("create_episode.html").render(
        langs=[
            {"label": "Primary (pt-BR)", "prefix": "primary"},
            {"label": "Secondary (en)", "prefix": "secondary"},
        ],
        primary="pt-BR",
        secondary_narration=enabled,
    )
    assert 'name="primary_narrate"' in html
    assert ('name="secondary_narrate"' in html) is enabled


class _Conn:
    def commit(self):
        pass


@pytest.fixture
def fake_repo(monkeypatch):
    """Stub the DB layer of POST /create/episode and record which episodes get narration queued."""
    queued: list[tuple[str, str]] = []

    @contextmanager
    def fake_get_conn(*_a, **_k):
        yield _Conn()

    monkeypatch.setattr(dash, "get_conn", fake_get_conn)
    monkeypatch.setattr(dash.repo, "create_manual_topic", lambda conn, title: "topic-1")
    monkeypatch.setattr(
        dash.repo,
        "upsert_draft",
        lambda conn, topic_id, ch, t, b, meta, language: f"draft-{language}",
    )
    monkeypatch.setattr(
        dash.repo,
        "upsert_episode",
        lambda conn, topic_id, draft_id, t, s, n, language, voice_id: f"ep-{language}",
    )
    monkeypatch.setattr(dash.repo, "record_review", lambda conn, **kw: None)
    monkeypatch.setattr(
        dash.repo,
        "enqueue_narration",
        lambda conn, episode_id, voice, script: queued.append((episode_id, script)),
    )
    return queued


def _post_create_episode(secondary_enabled: bool, monkeypatch) -> None:
    import asyncio

    monkeypatch.setenv("NARRATION_SECONDARY_ENABLED", "true" if secondary_enabled else "false")
    get_settings.cache_clear()
    asyncio.run(
        dash.create_episode(
            primary_title="Olá",
            primary_script="Roteiro em português.",
            primary_notes="",
            primary_narrate="1",
            primary_audio=None,
            secondary_title="Hello",
            secondary_script="English script.",
            secondary_notes="",
            secondary_narrate="1",
            secondary_audio=None,
            action="approve",
            _auth=None,
        )
    )


def test_create_episode_queues_english_narration_when_enabled(fake_repo, monkeypatch):
    _post_create_episode(True, monkeypatch)
    assert fake_repo == [("ep-pt-BR", "Roteiro em português."), ("ep-en", "English script.")]


def test_create_episode_ignores_english_narrate_when_disabled(fake_repo, monkeypatch):
    _post_create_episode(False, monkeypatch)
    assert fake_repo == [("ep-pt-BR", "Roteiro em português.")]
