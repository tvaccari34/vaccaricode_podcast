"""Tests for content generation helpers (pure — no network/DB)."""

from __future__ import annotations

from datetime import date

from boosternews.config import get_settings
from boosternews.generate import (
    append_subscribe_cta,
    assemble_blog_markdown,
    build_prompt,
    source_block,
    spoken_subscribe_url,
    strip_code_fences,
    subscribe_cta,
    subscribe_url,
)

TOPIC = {
    "id": "abc-123",
    "title": 'Rust 2.0 Released: "async" overhaul',
    "summary": "A major release.",
    "urls": ["https://example.com/rust", "https://news.ycombinator.com/item?id=1"],
    "extracted_text": "The Rust team shipped 2.0 today with long-awaited async improvements.",
}


def test_prompt_grounds_in_source_and_urls():
    p = build_prompt(TOPIC, "blog")
    assert "The Rust team shipped 2.0" in p  # article text included (grounding)
    assert "https://example.com/rust" in p  # source url included (attribution)
    assert "ground" in p.lower()  # grounding instruction present


def test_prompt_varies_by_format():
    assert "blog" in build_prompt(TOPIC, "blog")
    assert "podcast" in build_prompt(TOPIC, "podcast")
    assert "newsletter" in build_prompt(TOPIC, "newsletter")


def test_source_block_truncates_long_text():
    big = {"title": "t", "urls": [], "extracted_text": "x" * 10000}
    block = source_block(big)
    assert "[truncated]" in block
    assert len(block) < 10000


def test_blog_markdown_frontmatter_and_attribution():
    md = assemble_blog_markdown(
        TOPIC["title"],
        "Body paragraph.",
        TOPIC["urls"],
        "abc-123",
        today=date(2026, 6, 30),
    )
    assert md.startswith("---")
    assert "date: 2026-06-30" in md
    assert 'topic_id: "abc-123"' in md
    assert '\\"async\\"' in md  # title quotes are YAML-escaped
    # Attribution guaranteed even though the body didn't include a Sources section:
    assert "## Sources" in md
    assert "https://example.com/rust" in md
    assert "Body paragraph." in md


def test_blog_markdown_keeps_model_sources_section():
    body = "Intro.\n\n## Sources\n- [x](https://example.com/rust)"
    md = assemble_blog_markdown("T", body, ["https://example.com/rust"], "id1")
    assert md.count("## Sources") == 1  # not duplicated


def test_strip_code_fences():
    assert strip_code_fences("```markdown\nhello\n```") == "hello"
    assert strip_code_fences("```\nhi\n```") == "hi"
    assert strip_code_fences("plain text") == "plain text"


def test_subscribe_url_per_language():
    # pt-BR lives at the site root; secondary languages sit under /<code>.
    assert subscribe_url("pt-BR") == "http://localhost/subscribe"
    assert subscribe_url("en") == "http://localhost/en/subscribe"


def test_subscribe_cta_is_localized_and_linked():
    pt = subscribe_cta("pt-BR")
    en = subscribe_cta("en")
    assert "Assinar" in pt and "http://localhost/subscribe" in pt
    assert "Subscribe" in en and "http://localhost/en/subscribe" in en
    assert "{url}" not in pt  # template placeholder filled


def test_subscribe_cta_disabled(monkeypatch):
    from boosternews.config import get_settings

    monkeypatch.setenv("SUBSCRIBE_CTA_ENABLED", "false")
    get_settings.cache_clear()
    assert subscribe_cta("pt-BR") == ""


def test_append_subscribe_cta():
    out = append_subscribe_cta("Body.", "Subscribe: x")
    assert out == "Body.\n\n---\n\nSubscribe: x\n"  # rule-separated block
    assert append_subscribe_cta("Body.", "") == "Body."  # no-op when CTA empty


def test_spoken_subscribe_url_strips_scheme_for_narration():
    # The spoken outro reads the subscribe page aloud: no scheme, no UTM, no trailing slash.
    assert spoken_subscribe_url("pt-BR") == "localhost/subscribe"
    assert spoken_subscribe_url("en") == "localhost/en/subscribe"


def test_podcast_outro_is_mandatory_and_aligned_to_subscribe_page():
    get_settings.cache_clear()  # ignore any settings cached by an earlier test
    s = get_settings()
    # pt-BR outro sends listeners to the subscribe page (same destination as the show-notes CTA),
    # with the placeholder filled — the mandatory subscribe/share sign-off is present.
    pt = s.podcast_outro.format(url=spoken_subscribe_url(s.primary_language_code))
    assert "{url}" not in pt  # template placeholder filled
    assert "localhost/subscribe" in pt
    assert "assine a minha newsletter" in pt.lower()
    assert "compartilhe" in pt.lower()  # share invitation
    # English mirror uses the exact wording, under the /en subscribe page.
    en = s.podcast_outro_en.format(url=spoken_subscribe_url(s.secondary_language_code))
    assert "{url}" not in en
    assert "localhost/en/subscribe" in en
    assert "subscribe to my newsletter" in en.lower()
    assert "share it with them" in en.lower()
