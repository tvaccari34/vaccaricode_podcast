"""Default trend sources for the IT / software-development space.

Seeded into the ``sources`` table by ``boosternews seed-sources`` (idempotent — matched by name).
A nod to the project's inspiration: akitaonrails.com is included as a source.
"""

from __future__ import annotations

from psycopg.types.json import Json

DEFAULT_SOURCES: list[dict] = [
    {
        "name": "Hacker News Front Page",
        "kind": "hackernews",
        "url": "https://hn.algolia.com/api/v1/search",
        "config": {"tags": "front_page", "min_points": 50, "limit": 50, "weight": 1.2},
        "fetch_interval_minutes": 60,
    },
    {
        "name": "GitHub Trending (weekly)",
        "kind": "github_trending",
        "url": None,
        "config": {"since_days": 7, "min_stars": 150, "limit": 30, "weight": 1.0},
        "fetch_interval_minutes": 720,
    },
    {
        "name": "Lobsters",
        "kind": "rss",
        "url": "https://lobste.rs/rss",
        "config": {"limit": 40, "weight": 1.0},
        "fetch_interval_minutes": 120,
    },
    {
        "name": "InfoQ",
        "kind": "rss",
        "url": "https://feed.infoq.com/",
        "config": {"limit": 30, "weight": 0.9},
        "fetch_interval_minutes": 240,
    },
    {
        "name": "The Rust Blog",
        "kind": "rss",
        "url": "https://blog.rust-lang.org/feed.xml",
        "config": {"limit": 20, "weight": 0.9},
        "fetch_interval_minutes": 720,
    },
    {
        "name": "Martin Fowler",
        "kind": "rss",
        "url": "https://martinfowler.com/feed.atom",
        "config": {"limit": 20, "weight": 0.9},
        "fetch_interval_minutes": 720,
    },
    {
        "name": "AkitaOnRails",
        "kind": "rss",
        "url": "https://www.akitaonrails.com/index.xml",
        "config": {"limit": 20, "weight": 1.0},
        "fetch_interval_minutes": 360,
    },
]


def seed_default_sources() -> int:
    """Insert any default sources not already present (by name). Returns count inserted."""
    from .db import get_conn

    inserted = 0
    with get_conn() as conn:
        with conn.cursor() as cur:
            for s in DEFAULT_SOURCES:
                cur.execute("SELECT 1 FROM sources WHERE name = %s", (s["name"],))
                if cur.fetchone():
                    continue
                cur.execute(
                    "INSERT INTO sources (name, kind, url, config, enabled, fetch_interval_minutes) "
                    "VALUES (%s, %s, %s, %s, true, %s)",
                    (
                        s["name"],
                        s["kind"],
                        s.get("url"),
                        Json(s.get("config", {})),
                        s["fetch_interval_minutes"],
                    ),
                )
                inserted += 1
        conn.commit()
    return inserted
