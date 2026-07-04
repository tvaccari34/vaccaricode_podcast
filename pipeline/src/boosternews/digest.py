"""Weekly newsletter digest.

Instead of emailing one Listmonk campaign per published post, aggregate the posts published in the
last 7 days into a single campaign per language. Runs weekly (see the digest cron) or on demand via
``python -m boosternews digest``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from . import listmonk
from . import repository as repo
from .config import get_settings
from .db import get_conn

log = logging.getLogger("boosternews.digest")

WINDOW_DAYS = 7


def _lang_bits(language: str) -> tuple[str, str, str]:
    """(subject, intro, read-more label) for a language."""
    s = get_settings()
    if language == s.secondary_language_code:
        return s.newsletter_digest_subject_en, s.newsletter_digest_intro_en, "Read more"
    return s.newsletter_digest_subject, s.newsletter_digest_intro, "Leia mais"


def build_digest_body(items: list[dict], language: str) -> tuple[str, str]:
    """Compose the (subject, Markdown body) for a language's weekly digest. Pure and testable."""
    subject, intro, read_more = _lang_bits(language)
    parts = [intro, ""]
    for it in items:
        parts.append(f"## {it['title']}")
        if it.get("blurb"):
            parts.append(it["blurb"].strip())
        if it.get("url"):
            parts.append(f"[{read_more}]({it['url']})")
        parts.append("")
    return subject, "\n\n".join(parts).strip() + "\n"


def run_digest(now: datetime | None = None) -> dict[str, str]:
    """Create the weekly digest campaign per language for posts since the last digest (<= 7 days).

    Idempotent: the window starts at the previous digest's end, so posts are never included twice
    and a language with no new posts is skipped (no campaign, no digest row).
    """
    s = get_settings()
    now = now or datetime.now(timezone.utc)
    floor = now - timedelta(days=WINDOW_DAYS)
    languages = [s.primary_language_code]
    if s.secondary_language_code:
        languages.append(s.secondary_language_code)

    summary: dict[str, str] = {}
    for lang in languages:
        last = repo.last_digest_end(lang)
        window_start = max(last, floor) if last else floor
        items = repo.posts_for_digest(lang, window_start)
        if not items:
            summary[lang] = "no new posts — skipped"
            continue

        subject, body = build_digest_body(items, lang)
        try:
            cid = listmonk.create_campaign(
                name=f"Weekly digest {now:%Y-%m-%d} [{lang}]",
                subject=subject,
                body=body,
                list_id=listmonk.list_id_for(lang),
            )
        except Exception as exc:  # noqa: BLE001 — never let one language abort the others
            log.warning("digest campaign failed (%s): %s", lang, exc)
            summary[lang] = f"campaign failed: {exc}"
            continue

        if not cid:
            # Listmonk not configured → leave the window open so nothing is lost.
            summary[lang] = "Listmonk not configured — skipped"
            continue

        sent = False
        if s.newsletter_digest_autosend:
            try:
                sent = listmonk.start_campaign(cid)
            except Exception as exc:  # noqa: BLE001
                log.warning("digest auto-send failed (%s): %s", lang, exc)

        with get_conn() as conn:
            repo.record_digest(conn, lang, cid, len(items), window_start, now)
            conn.commit()
        summary[lang] = f"{len(items)} post(s) → campaign #{cid} ({'sent' if sent else 'draft'})"

    log.info("weekly digest: %s", summary)
    return summary
