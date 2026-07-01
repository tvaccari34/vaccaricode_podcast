"""Hacker News source fetcher (Algolia API).

Uses the public HN Search (Algolia) API, which returns front-page / search hits with points and
timestamps. Story comments-only items (no URL) fall back to the HN item permalink.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..models import SourceItem, SourceRow

DEFAULT_ENDPOINT = "https://hn.algolia.com/api/v1/search"


def items_from_hn(payload: dict, min_points: int = 0) -> list[SourceItem]:
    """Pure transform of an Algolia response into SourceItems."""
    items: list[SourceItem] = []
    for hit in payload.get("hits", []):
        title = hit.get("title") or hit.get("story_title")
        if not title:
            continue
        points = int(hit.get("points") or 0)
        if points < min_points:
            continue
        object_id = hit.get("objectID")
        url = hit.get("url") or hit.get("story_url")
        if not url and object_id:
            url = f"https://news.ycombinator.com/item?id={object_id}"
        if not url:
            continue
        published = None
        if hit.get("created_at_i"):
            published = datetime.fromtimestamp(int(hit["created_at_i"]), tz=timezone.utc)
        items.append(
            SourceItem(
                title=title.strip(),
                url=url,
                external_id=f"hn-{object_id}" if object_id else url,
                engagement=points,
                published_at=published,
                extra={"comments": int(hit.get("num_comments") or 0)},
            )
        )
    return items


def fetch_hackernews(source: SourceRow) -> list[SourceItem]:
    cfg = source.config
    endpoint = source.url or DEFAULT_ENDPOINT
    params = {
        "tags": cfg.get("tags", "front_page"),
        "hitsPerPage": int(cfg.get("limit", 50)),
    }
    if cfg.get("query"):
        params["query"] = cfg["query"]
    resp = httpx.get(endpoint, params=params, timeout=30)
    resp.raise_for_status()
    return items_from_hn(resp.json(), int(cfg.get("min_points", 0)))
