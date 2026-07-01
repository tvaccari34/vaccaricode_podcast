"""RSS / Atom source fetcher (feedparser)."""

from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
import re

import feedparser

from ..models import SourceItem, SourceRow

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_summary(text: str | None) -> str | None:
    if not text:
        return None
    return unescape(_TAG_RE.sub("", text)).strip() or None


def _entry_datetime(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        value = getattr(entry, attr, None)
        if value:
            # feedparser returns a time.struct_time in UTC
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def items_from_parsed(parsed, limit: int) -> list[SourceItem]:
    """Pure transform of a parsed feed into SourceItems (no network)."""
    items: list[SourceItem] = []
    for entry in parsed.entries[:limit]:
        link = getattr(entry, "link", None)
        title = getattr(entry, "title", None)
        if not link or not title:
            continue
        items.append(
            SourceItem(
                title=title.strip(),
                url=link.strip(),
                external_id=getattr(entry, "id", None) or link.strip(),
                summary=_clean_summary(getattr(entry, "summary", None)),
                published_at=_entry_datetime(entry),
            )
        )
    return items


def fetch_rss(source: SourceRow) -> list[SourceItem]:
    if not source.url:
        return []
    limit = int(source.config.get("limit", 50))
    parsed = feedparser.parse(source.url)
    return items_from_parsed(parsed, limit)
