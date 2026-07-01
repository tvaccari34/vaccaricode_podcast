"""Tests for content generation helpers (pure — no network/DB)."""

from __future__ import annotations

from datetime import date

from boosternews.generate import (
    assemble_blog_markdown,
    build_prompt,
    source_block,
    strip_code_fences,
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
