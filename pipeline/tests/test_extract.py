"""Tests for article text extraction (no network)."""

from __future__ import annotations

from boosternews.extract import extract_text_from_html

ARTICLE_HTML = """
<html><head><title>A Big Day for Rust</title></head>
<body>
  <nav>home about login</nav>
  <article>
    <h1>A Big Day for Rust</h1>
    <p>The Rust team announced a major release today, bringing long-awaited improvements to
    the async ecosystem and the borrow checker. Developers have been waiting for these changes
    for a long time and the response has been overwhelmingly positive across the community.</p>
    <p>In addition to async improvements, the release includes faster compile times and better
    diagnostics. Maintainers say the work represents months of collaboration between hundreds of
    contributors from around the world.</p>
  </article>
  <footer>copyright 2026</footer>
</body></html>
"""


def test_extracts_main_body():
    text = extract_text_from_html(ARTICLE_HTML)
    assert text is not None
    assert "major release" in text
    # Boilerplate nav/footer should be excluded.
    assert "login" not in text


def test_empty_html_returns_none():
    assert extract_text_from_html("") is None
    assert extract_text_from_html(None) is None
