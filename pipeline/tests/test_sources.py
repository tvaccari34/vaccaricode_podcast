"""Tests for source parsers (pure transforms, no network)."""

from __future__ import annotations

import feedparser

from boosternews.sources.github import items_from_github
from boosternews.sources.hackernews import items_from_hn
from boosternews.sources.rss import items_from_parsed

RSS_XML = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>Example Dev Feed</title>
  <item>
    <title>Shiny New Framework 1.0</title>
    <link>https://example.com/shiny</link>
    <guid>https://example.com/shiny</guid>
    <description>&lt;p&gt;A &lt;b&gt;great&lt;/b&gt; framework.&lt;/p&gt;</description>
    <pubDate>Mon, 29 Jun 2026 10:00:00 GMT</pubDate>
  </item>
  <item>
    <title>No Link Item</title>
  </item>
</channel></rss>
"""


def test_rss_parsing_maps_and_skips_invalid():
    parsed = feedparser.parse(RSS_XML)
    items = items_from_parsed(parsed, limit=10)
    assert len(items) == 1  # the link-less item is skipped
    it = items[0]
    assert it.title == "Shiny New Framework 1.0"
    assert it.url == "https://example.com/shiny"
    assert it.summary == "A great framework."  # HTML stripped + unescaped
    assert it.published_at is not None


def test_hackernews_filters_by_points_and_builds_url():
    payload = {
        "hits": [
            {
                "title": "Popular Story",
                "url": "https://ex.com/a",
                "objectID": "1",
                "points": 120,
                "created_at_i": 1751280000,
                "num_comments": 40,
            },
            {
                "title": "Unpopular",
                "url": "https://ex.com/b",
                "objectID": "2",
                "points": 3,
            },
            {"title": "Ask HN: no url", "objectID": "3", "points": 80},
        ]
    }
    items = items_from_hn(payload, min_points=50)
    titles = [i.title for i in items]
    assert "Popular Story" in titles and "Unpopular" not in titles
    ask = next(i for i in items if i.title.startswith("Ask HN"))
    assert ask.url == "https://news.ycombinator.com/item?id=3"  # permalink fallback
    pop = next(i for i in items if i.title == "Popular Story")
    assert pop.engagement == 120


def test_github_maps_stars_to_engagement():
    payload = {
        "items": [
            {
                "id": 9,
                "full_name": "acme/rocket",
                "html_url": "https://github.com/acme/rocket",
                "description": "Fast things",
                "stargazers_count": 4200,
                "language": "Rust",
                "created_at": "2026-06-25T00:00:00Z",
            },
            {"id": 10, "full_name": "no/url"},  # missing html_url → skipped
        ]
    }
    items = items_from_github(payload)
    assert len(items) == 1
    it = items[0]
    assert it.engagement == 4200
    assert it.url == "https://github.com/acme/rocket"
    assert "Fast things" in it.title
    assert it.extra["language"] == "Rust"
