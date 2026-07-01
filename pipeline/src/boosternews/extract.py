"""Article text extraction (trafilatura).

Pulls the main readable body out of a candidate's source URL so generation can be grounded in
the actual article rather than just the headline. Network fetch is separated from parsing so the
parsing path is unit-testable without network.
"""

from __future__ import annotations

import logging

import trafilatura

log = logging.getLogger("boosternews.extract")


def extract_text_from_html(html: str | None) -> str | None:
    """Extract main article text from raw HTML. Returns None if nothing usable is found."""
    if not html:
        return None
    return trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        favor_recall=True,
    )


def extract_text(url: str) -> str | None:
    """Fetch ``url`` and extract its main article text. Returns None on failure."""
    try:
        downloaded = trafilatura.fetch_url(url)
    except Exception as exc:  # noqa: BLE001 — network errors are expected; skip the item
        log.warning("fetch failed for %s: %s", url, exc)
        return None
    return extract_text_from_html(downloaded)
