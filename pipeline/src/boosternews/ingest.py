"""Trend ingestion job.

One pass over the due (or all) enabled sources: fetch candidate items, score them, and
upsert/merge them into the ``topics`` queue. Each source is isolated — a failing source is
logged and skipped without aborting the run or affecting other sources' persisted candidates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .db import get_conn
from .dedup import dedup_key
from .extract import extract_text
from .repository import (
    load_sources,
    mark_source_fetched,
    set_extracted_text,
    topics_missing_text,
    upsert_topic,
)
from .scoring import score_item
from .sources import get_fetcher

log = logging.getLogger("boosternews.ingest")


@dataclass
class SourceResult:
    name: str
    status: str  # "ok" | "error"
    created: int = 0
    merged: int = 0
    detail: str = ""


def run_ingest(
    *, only_due: bool = True, source_name: str | None = None, extract: bool = False
) -> list[SourceResult]:
    """Run one ingestion pass. Returns a per-source summary."""
    sources = load_sources(only_due=only_due, name=source_name)
    if not sources:
        log.info("no sources due")
        return []

    results: list[SourceResult] = []
    for src in sources:
        try:
            fetcher = get_fetcher(src.kind)
            items = fetcher(src)
        except Exception as exc:  # noqa: BLE001 — isolate per-source failures
            log.warning("source '%s' failed: %s", src.name, exc)
            results.append(SourceResult(src.name, "error", detail=str(exc)))
            continue

        weight = float(src.config.get("weight", 1.0))
        created = merged = 0
        # One transaction per source so a mid-source error can't discard other sources' work.
        with get_conn() as conn:
            for item in items:
                topic_id, is_new = upsert_topic(
                    conn,
                    title=item.title,
                    summary=item.summary,
                    url=item.url,
                    source_id=src.id,
                    dkey=dedup_key(item.title),
                    base_score=score_item(item, source_weight=weight),
                    published_at=item.published_at,
                )
                if is_new:
                    created += 1
                    if extract:
                        text = extract_text(item.url)
                        if text:
                            set_extracted_text(conn, topic_id, text)
                else:
                    merged += 1
            mark_source_fetched(conn, src.id)
            conn.commit()

        log.info("source '%s': %d new, %d merged", src.name, created, merged)
        results.append(SourceResult(src.name, "ok", created=created, merged=merged))
    return results


def run_extraction(limit: int = 25) -> int:
    """Backfill article text for topics that still lack it. Returns count extracted."""
    extracted = 0
    for topic_id, url in topics_missing_text(limit):
        text = extract_text(url)
        if not text:
            continue
        with get_conn() as conn:
            set_extracted_text(conn, topic_id, text)
            conn.commit()
        extracted += 1
        log.info("extracted text for topic %s", topic_id)
    return extracted
