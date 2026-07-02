"""Database access for trend discovery (sources + topics)."""

from __future__ import annotations

import psycopg
from psycopg.types.json import Json

from .models import SourceRow
from .scoring import topic_score


# ── Sources ────────────────────────────────────────────────────────────────
def load_sources(*, only_due: bool = True, name: str | None = None) -> list[SourceRow]:
    """Return enabled sources, optionally only those due per their fetch interval."""
    clauses = ["enabled = true"]
    params: list = []
    if name:
        clauses.append("name = %s")
        params.append(name)
    if only_due:
        clauses.append(
            "(last_fetched_at IS NULL "
            "OR last_fetched_at < now() - make_interval(mins => fetch_interval_minutes))"
        )
    sql = (
        "SELECT id, name, kind, url, config, enabled, fetch_interval_minutes, last_fetched_at "
        f"FROM sources WHERE {' AND '.join(clauses)} ORDER BY name"
    )
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return [
            SourceRow(
                id=str(r[0]),
                name=r[1],
                kind=r[2],
                url=r[3],
                config=r[4] or {},
                enabled=r[5],
                fetch_interval_minutes=r[6],
                last_fetched_at=r[7],
            )
            for r in cur.fetchall()
        ]


def mark_source_fetched(conn: psycopg.Connection, source_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE sources SET last_fetched_at = now() WHERE id = %s", (source_id,))


# ── Topics (candidate queue) ────────────────────────────────────────────────
def upsert_topic(
    conn: psycopg.Connection,
    *,
    title: str,
    summary: str | None,
    url: str,
    source_id: str,
    dkey: str,
    base_score: float,
    published_at=None,
) -> tuple[str, bool]:
    """Insert a new topic or merge into an existing one with the same dedup key.

    Returns ``(topic_id, created)`` where ``created`` is True for a fresh insert.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, urls, source_ids, base_score FROM topics WHERE dedup_key = %s FOR UPDATE",
            (dkey,),
        )
        row = cur.fetchone()
        if row:
            topic_id, urls, source_ids, existing_base = row
            new_urls = _union(urls, url)
            new_source_ids = _union([str(s) for s in (source_ids or [])], source_id)
            base = max(existing_base or 0.0, base_score)
            cur.execute(
                "UPDATE topics SET urls = %s, source_ids = %s::uuid[], "
                "summary = COALESCE(summary, %s), base_score = %s, score = %s, updated_at = now() "
                "WHERE id = %s",
                (
                    new_urls,
                    new_source_ids,
                    summary,
                    base,
                    topic_score(base, len(new_source_ids)),
                    topic_id,
                ),
            )
            return str(topic_id), False

        cur.execute(
            "INSERT INTO topics (title, summary, urls, source_ids, dedup_key, base_score, score, "
            "status, first_seen_at) "
            "VALUES (%s, %s, %s, %s::uuid[], %s, %s, %s, 'new', COALESCE(%s, now())) RETURNING id",
            (
                title,
                summary,
                [url],
                [source_id],
                dkey,
                base_score,
                topic_score(base_score, 1),
                published_at,
            ),
        )
        return str(cur.fetchone()[0]), True


def set_extracted_text(conn: psycopg.Connection, topic_id: str, text: str) -> None:
    """Store extracted article text if the topic doesn't already have some."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE topics SET extracted_text = %s, updated_at = now() "
            "WHERE id = %s AND (extracted_text IS NULL OR extracted_text = '')",
            (text, topic_id),
        )


def topics_missing_text(limit: int = 25) -> list[tuple[str, str]]:
    """Return ``(topic_id, url)`` for topics that still need extraction."""
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, urls[1] FROM topics "
            "WHERE (extracted_text IS NULL OR extracted_text = '') AND array_length(urls, 1) >= 1 "
            "ORDER BY score DESC LIMIT %s",
            (limit,),
        )
        return [(str(r[0]), r[1]) for r in cur.fetchall()]


def list_topics(*, limit: int = 20, status: str | None = None) -> list[dict]:
    from .db import get_conn

    clause = "WHERE status = %s" if status else ""
    params: list = [status] if status else []
    params.append(limit)
    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT title, score, status, COALESCE(array_length(source_ids, 1), 0), urls[1], "
            "(extracted_text IS NOT NULL) "
            f"FROM topics {clause} ORDER BY score DESC, first_seen_at DESC LIMIT %s",
            params,
        )
        return [
            {
                "title": r[0],
                "score": r[1],
                "status": r[2],
                "sources": r[3],
                "url": r[4],
                "has_text": r[5],
            }
            for r in cur.fetchall()
        ]


def _union(existing: list | None, value: str) -> list:
    """Append value to a list preserving order and uniqueness."""
    out = list(existing or [])
    if value not in out:
        out.append(value)
    return out


# ── Generation: topics + drafts + episodes ──────────────────────────────────
def get_topic(topic_id: str) -> dict | None:
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, summary, urls, extracted_text, score, status "
            "FROM topics WHERE id = %s",
            (topic_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": str(r[0]),
            "title": r[1],
            "summary": r[2],
            "urls": list(r[3] or []),
            "extracted_text": r[4],
            "score": r[5],
            "status": r[6],
        }


def pick_top_new_topic() -> str | None:
    """Highest-scoring 'new' topic that already has extracted article text."""
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM topics "
            "WHERE status = 'new' AND extracted_text IS NOT NULL AND extracted_text <> '' "
            "ORDER BY score DESC LIMIT 1"
        )
        r = cur.fetchone()
        return str(r[0]) if r else None


def upsert_draft(
    conn: psycopg.Connection,
    topic_id: str,
    channel: str,
    title: str,
    body: str,
    metadata: dict,
    language: str = "pt-BR",
) -> str:
    """Insert or replace the draft for (topic, channel, language); resets it to pending_review."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO drafts (topic_id, channel, language, title, body, metadata, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, 'pending_review') "
            "ON CONFLICT (topic_id, channel, language) DO UPDATE SET "
            "title = EXCLUDED.title, body = EXCLUDED.body, metadata = EXCLUDED.metadata, "
            "status = 'pending_review', updated_at = now() RETURNING id",
            (topic_id, channel, language, title, body, Json(metadata)),
        )
        return str(cur.fetchone()[0])


def upsert_episode(
    conn: psycopg.Connection,
    topic_id: str,
    draft_id: str,
    title: str,
    script: str,
    show_notes: str,
    language: str = "pt-BR",
    voice_id: str | None = None,
) -> str:
    """Create or update the episode for a (topic, language)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM episodes WHERE topic_id = %s AND language = %s", (topic_id, language)
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE episodes SET draft_id = %s, title = %s, script = %s, show_notes = %s, "
                "voice_id = %s, status = 'script_ready', updated_at = now() WHERE id = %s",
                (draft_id, title, script, show_notes, voice_id, row[0]),
            )
            return str(row[0])
        cur.execute(
            "INSERT INTO episodes (topic_id, draft_id, language, title, script, show_notes, "
            "voice_id, status) VALUES (%s, %s, %s, %s, %s, %s, %s, 'script_ready') RETURNING id",
            (topic_id, draft_id, language, title, script, show_notes, voice_id),
        )
        return str(cur.fetchone()[0])


def set_topic_status(conn: psycopg.Connection, topic_id: str, status: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE topics SET status = %s, updated_at = now() WHERE id = %s",
            (status, topic_id),
        )


def list_drafts(*, limit: int = 20, channel: str | None = None) -> list[dict]:
    from .db import get_conn

    clause = "WHERE channel = %s" if channel else ""
    params: list = [channel] if channel else []
    params.append(limit)
    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT channel, status, title, length(body), topic_id "
            f"FROM drafts {clause} ORDER BY updated_at DESC LIMIT %s",
            params,
        )
        return [
            {
                "channel": r[0],
                "status": r[1],
                "title": r[2],
                "chars": r[3],
                "topic_id": str(r[4]),
            }
            for r in cur.fetchall()
        ]


def get_draft_body(topic_id: str, channel: str, language: str = "pt-BR") -> str | None:
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT body FROM drafts WHERE topic_id = %s AND channel = %s AND language = %s",
            (topic_id, channel, language),
        )
        r = cur.fetchone()
        return r[0] if r else None


def list_secondary_episodes(limit: int = 50) -> list[dict]:
    """Episodes in a non-primary language (manual audio): id, language, title, status, audio."""
    from .config import get_settings
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT e.id, e.language, e.title, e.status, e.audio_url, e.duration_seconds "
            "FROM episodes e JOIN topics t ON t.id = e.topic_id "
            "WHERE e.language <> %s ORDER BY t.score DESC, e.updated_at DESC LIMIT %s",
            (get_settings().primary_language_code, limit),
        )
        return [
            {
                "id": str(r[0]),
                "language": r[1],
                "title": r[2],
                "status": r[3],
                "audio_url": r[4],
                "duration": r[5],
            }
            for r in cur.fetchall()
        ]


def list_primary_episodes(limit: int = 50) -> list[dict]:
    """Auto-narrated (primary-language) episodes for the dashboard's edit-script & re-narrate
    section — independent of the review queue, so published episodes stay editable."""
    from .config import get_settings
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT e.id, e.title, e.status, e.audio_url, e.duration_seconds, e.script "
            "FROM episodes e JOIN topics t ON t.id = e.topic_id "
            "WHERE e.language = %s ORDER BY t.score DESC, e.updated_at DESC LIMIT %s",
            (get_settings().primary_language_code, limit),
        )
        return [
            {
                "id": str(r[0]),
                "title": r[1],
                "status": r[2],
                "audio_url": r[3],
                "duration": r[4],
                "script": r[5],
            }
            for r in cur.fetchall()
        ]


def episode_audio_target_status(conn: psycopg.Connection, episode_id: str) -> str:
    """Status an episode should take once its audio is (re)generated.

    Re-narrating an already-published episode must keep it live, so return ``'published'`` when the
    episode's podcast draft is already published; otherwise ``'ready'`` (first narration, still
    awaiting review/publish).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM drafts d JOIN episodes e "
            "ON e.topic_id = d.topic_id AND e.language = d.language "
            "WHERE e.id = %s AND d.channel = 'podcast' AND d.status = 'published')",
            (episode_id,),
        )
        return "published" if cur.fetchone()[0] else "ready"


def get_episode(episode_id: str) -> dict | None:
    """Fetch an episode by id (script, language, title, audio) — used by the dashboard."""
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, topic_id, language, title, script, show_notes, audio_url, status "
            "FROM episodes WHERE id = %s",
            (episode_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": str(r[0]),
            "topic_id": str(r[1]),
            "language": r[2],
            "title": r[3],
            "script": r[4],
            "show_notes": r[5],
            "audio_url": r[6],
            "status": r[7],
        }


# ── Review workflow ─────────────────────────────────────────────────────────
def get_review_queue(limit: int = 50) -> list[dict]:
    """Topics that have at least one draft awaiting review (pending_review or needs_edit)."""
    from .db import get_conn

    out: list[dict] = []
    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT t.id, t.title, t.score FROM topics t "
            "WHERE EXISTS (SELECT 1 FROM drafts d WHERE d.topic_id = t.id "
            "             AND d.status IN ('pending_review', 'needs_edit')) "
            "ORDER BY t.score DESC LIMIT %s",
            (limit,),
        )
        topics = cur.fetchall()
        for tid, title, score in topics:
            cur.execute(
                "SELECT language, channel, id, status, body FROM drafts WHERE topic_id = %s "
                "ORDER BY language, channel",
                (tid,),
            )
            langs: dict[str, dict] = {}
            for lang, channel, did, status, body in cur.fetchall():
                langs.setdefault(lang, {"drafts": {}, "episode": None})
                langs[lang]["drafts"][channel] = {"id": str(did), "status": status, "body": body}
            cur.execute(
                "SELECT language, id, status, audio_url, duration_seconds, script FROM episodes "
                "WHERE topic_id = %s",
                (tid,),
            )
            for lang, eid, status, audio_url, duration, script in cur.fetchall():
                langs.setdefault(lang, {"drafts": {}, "episode": None})
                langs[lang]["episode"] = {
                    "id": str(eid),
                    "status": status,
                    "audio_url": audio_url,
                    "duration": duration,
                    "script": script,
                }
            out.append({"topic_id": str(tid), "title": title, "score": score, "langs": langs})
    return out


def record_review(
    conn: psycopg.Connection,
    *,
    topic_id: str,
    channel: str,
    decision: str,
    reviewer: str,
    notes: str | None = None,
    language: str = "pt-BR",
) -> None:
    """Record a per-channel review decision and apply the resulting status transition."""
    from .review import decision_to_status

    new_status = decision_to_status(decision)  # validates the decision
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM drafts WHERE topic_id = %s AND channel = %s AND language = %s",
            (topic_id, channel, language),
        )
        row = cur.fetchone()
        draft_id = row[0] if row else None

        episode_id = None
        if channel == "podcast":
            cur.execute(
                "SELECT id FROM episodes WHERE topic_id = %s AND language = %s",
                (topic_id, language),
            )
            er = cur.fetchone()
            episode_id = er[0] if er else None

        cur.execute(
            "INSERT INTO reviews (draft_id, episode_id, channel, decision, reviewer, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (draft_id, episode_id, channel, decision, reviewer, notes),
        )
        if draft_id:
            cur.execute(
                "UPDATE drafts SET status = %s, updated_at = now() WHERE id = %s",
                (new_status, draft_id),
            )
        if episode_id and decision == "approve":
            cur.execute(
                "UPDATE episodes SET status = 'approved', updated_at = now() WHERE id = %s",
                (episode_id,),
            )


def publish_draft(conn: psycopg.Connection, draft_id: str) -> str:
    """Publish an approved draft (enforces the approval gate). Returns its channel."""
    from .review import assert_publishable

    with conn.cursor() as cur:
        cur.execute("SELECT status, channel FROM drafts WHERE id = %s FOR UPDATE", (draft_id,))
        row = cur.fetchone()
        if not row:
            from .review import PublishGateError

            raise PublishGateError(f"draft {draft_id} not found")
        status, channel = row
        assert_publishable(status)  # raises PublishGateError unless 'approved'
        cur.execute(
            "UPDATE drafts SET status = 'published', updated_at = now() WHERE id = %s",
            (draft_id,),
        )
        return channel


# ── Publishing ──────────────────────────────────────────────────────────────
def get_topic_drafts(topic_id: str) -> list[dict]:
    """Return a topic's drafts across all channels + languages."""
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT channel, language, id, status, title, body FROM drafts WHERE topic_id = %s",
            (topic_id,),
        )
        return [
            {
                "channel": r[0],
                "language": r[1],
                "id": str(r[2]),
                "status": r[3],
                "title": r[4],
                "body": r[5],
            }
            for r in cur.fetchall()
        ]


def publish_episode(conn: psycopg.Connection, topic_id: str, language: str = "pt-BR") -> None:
    """Mark a (topic, language) episode published (when its podcast draft is published)."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE episodes SET status = 'published', updated_at = now() "
            "WHERE topic_id = %s AND language = %s",
            (topic_id, language),
        )


def record_publication(
    conn: psycopg.Connection,
    topic_id: str,
    channel: str,
    ref_id: str,
    url: str | None,
    external_id: str | None = None,
    language: str = "pt-BR",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO publications (topic_id, channel, ref_id, url, external_id, language) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (topic_id, channel, ref_id, url, external_id, language),
        )


def topics_with_approved() -> list[str]:
    """Topic ids that have at least one approved (not-yet-published) draft."""
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("SELECT DISTINCT topic_id FROM drafts WHERE status = 'approved'")
        return [str(r[0]) for r in cur.fetchall()]


def enqueue_narration(
    conn: psycopg.Connection, episode_id: str, voice_id: str, text: str
) -> str | None:
    """Queue a narration job for an episode, unless one is already active. Returns job id or None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM narration_jobs WHERE episode_id = %s AND status IN ('queued', 'claimed')",
            (episode_id,),
        )
        if cur.fetchone():
            return None
        cur.execute(
            "INSERT INTO narration_jobs (episode_id, voice_id, text, status) "
            "VALUES (%s, %s, %s, 'queued') RETURNING id",
            (episode_id, voice_id, text),
        )
        return str(cur.fetchone()[0])


def claim_next_job(conn: psycopg.Connection, worker_id: str) -> dict | None:
    """Atomically claim the oldest queued narration job. Returns the job or None."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, episode_id, voice_id, text FROM narration_jobs "
            "WHERE status = 'queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            return None
        cur.execute(
            "UPDATE narration_jobs SET status = 'claimed', claimed_by = %s, claimed_at = now(), "
            "attempts = attempts + 1 WHERE id = %s",
            (worker_id, row[0]),
        )
        return {
            "id": str(row[0]),
            "episode_id": str(row[1]),
            "voice_id": row[2],
            "text": row[3],
        }


def get_job(conn: psycopg.Connection, job_id: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, episode_id, status, attempts, max_attempts FROM narration_jobs WHERE id = %s",
            (job_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": str(r[0]),
            "episode_id": str(r[1]),
            "status": r[2],
            "attempts": r[3],
            "max_attempts": r[4],
        }


def complete_job(conn: psycopg.Connection, job_id: str, result_key: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE narration_jobs SET status = 'completed', result_audio_key = %s, "
            "updated_at = now() WHERE id = %s",
            (result_key, job_id),
        )


def fail_job(conn: psycopg.Connection, job_id: str, error: str) -> str:
    """Mark a job failed; requeue it if attempts remain, else fail for good. Returns new status."""
    from .jobs import next_status_after_failure

    with conn.cursor() as cur:
        cur.execute(
            "SELECT attempts, max_attempts FROM narration_jobs WHERE id = %s FOR UPDATE",
            (job_id,),
        )
        row = cur.fetchone()
        if not row:
            return "missing"
        new_status = next_status_after_failure(row[0], row[1])
        cur.execute(
            "UPDATE narration_jobs SET status = %s, error = %s, updated_at = now() WHERE id = %s",
            (new_status, error, job_id),
        )
        return new_status


def update_episode_audio(
    conn: psycopg.Connection,
    episode_id: str,
    audio_url: str,
    duration_seconds: int,
    file_size_bytes: int,
    status: str = "ready",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE episodes SET audio_url = %s, duration_seconds = %s, file_size_bytes = %s, "
            "status = %s, updated_at = now() WHERE id = %s",
            (audio_url, duration_seconds, file_size_bytes, status, episode_id),
        )


def update_script_and_renarrate(
    conn: psycopg.Connection, episode_id: str, new_script: str
) -> str | None:
    """Replace an episode's narration script, drop its stale audio, and queue a fresh narration job.

    Used by the dashboard's "edit script & re-narrate" action. Any prior jobs for the episode are
    retired to ``failed`` (the narration_status enum has no 'superseded'), so the queue reflects
    only the new job. Returns the new job id, or ``None`` if the episode doesn't exist.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT voice_id FROM episodes WHERE id = %s", (episode_id,))
        row = cur.fetchone()
        if not row:
            return None
        voice_id = row[0] or "tiago"
        cur.execute(
            "UPDATE episodes SET script = %s, audio_url = NULL, duration_seconds = NULL, "
            "file_size_bytes = NULL, status = 'script_ready', updated_at = now() WHERE id = %s",
            (new_script, episode_id),
        )
        cur.execute(
            "UPDATE narration_jobs SET status = 'failed', updated_at = now() "
            "WHERE episode_id = %s AND status IN ('queued', 'claimed', 'completed')",
            (episode_id,),
        )
        cur.execute(
            "INSERT INTO narration_jobs (episode_id, voice_id, text, status) "
            "VALUES (%s, %s, %s, 'queued') RETURNING id",
            (episode_id, voice_id, new_script),
        )
        return str(cur.fetchone()[0])


def list_narration_jobs(limit: int = 20) -> list[dict]:
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT n.status, n.attempts, n.max_attempts, e.title, n.error "
            "FROM narration_jobs n JOIN episodes e ON e.id = n.episode_id "
            "ORDER BY n.created_at DESC LIMIT %s",
            (limit,),
        )
        return [
            {
                "status": r[0],
                "attempts": r[1],
                "max_attempts": r[2],
                "title": r[3],
                "error": r[4],
            }
            for r in cur.fetchall()
        ]


def episodes_needing_narration() -> list[tuple[str, str, str]]:
    """Episodes with a script but no audio and no active job. Returns (episode_id, voice_id, script)."""
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, COALESCE(voice_id, ''), script FROM episodes e "
            "WHERE audio_url IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM narration_jobs n "
            "                WHERE n.episode_id = e.id AND n.status IN ('queued', 'claimed', 'completed'))"
        )
        return [(str(r[0]), r[1], r[2]) for r in cur.fetchall()]


def list_publications(limit: int = 20) -> list[dict]:
    from .db import get_conn

    with get_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT channel, url, external_id, published_at FROM publications "
            "ORDER BY published_at DESC LIMIT %s",
            (limit,),
        )
        return [
            {"channel": r[0], "url": r[1], "external_id": r[2], "published_at": r[3]}
            for r in cur.fetchall()
        ]
