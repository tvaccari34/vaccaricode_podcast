"""Deduplication: a stable key that collapses the same story across sources.

The key is derived from a normalized title (lowercased, accents stripped, punctuation removed,
common stopwords dropped). Two headlines describing the same story tend to normalize to the same
token set and therefore the same key, which the upsert uses to merge them into one topic.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

_WORD_RE = re.compile(r"[a-z0-9]+")

# Small stopword set — enough to absorb trivial phrasing differences without over-merging.
_STOPWORDS = frozenset("""
    a an the of to in on for and or with is are was were be been being it its this that these
    those as at by from has have had will would can could should new now how why what whats
    using use vs via about into over under after before your you our their his her my i we they
    """.split())


def normalize_title(title: str) -> str:
    """Return a normalized token string for a title."""
    folded = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    # Drop stopwords and single-character tokens (e.g. the stray "s" from possessives, or "2"/"0"
    # from version numbers) so trivial phrasing differences collapse to the same key.
    tokens = [t for t in _WORD_RE.findall(folded.lower()) if len(t) > 1 and t not in _STOPWORDS]
    return " ".join(tokens)


def dedup_key(title: str) -> str:
    """Return a hex digest identifying a story by its normalized title."""
    return hashlib.sha1(normalize_title(title).encode("utf-8")).hexdigest()
