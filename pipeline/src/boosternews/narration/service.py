"""Shared narration completion + the VPS-side drainer for cloud TTS providers.

`complete_narration` is the single downstream path (store raw → ffmpeg assemble → store mp3 →
attach to episode → complete job → queue rebuild), used by both the home-worker upload (the
`/complete` route) and the VPS drainer. `drain_once` is the server-side queue processor used when a
cloud provider (elevenlabs/custom) is active.
"""

from __future__ import annotations

import logging
import os
import tempfile

from .. import audio
from .. import repository as repo
from .. import storage
from ..config import get_settings
from ..db import get_conn
from ..tts import get_provider, voice_for

log = logging.getLogger("boosternews.narration.service")


def complete_narration(episode_id: str, job_id: str, raw_audio: bytes) -> dict:
    """Assemble + store the episode audio from raw narration bytes, and finish the job."""
    settings = get_settings()
    storage.ensure_bucket()
    storage.upload_bytes(raw_audio, f"narration/{episode_id}/raw.wav", content_type="audio/wav")

    intro = settings.audio_intro_path or None
    outro = settings.audio_outro_path or None
    with tempfile.TemporaryDirectory() as tmp:
        raw_path = os.path.join(tmp, "raw")  # ffmpeg detects the format from content
        out_path = os.path.join(tmp, "episode.mp3")
        with open(raw_path, "wb") as fh:
            fh.write(raw_audio)
        duration, size = audio.assemble(
            raw_path,
            out_path,
            intro=intro if intro and os.path.exists(intro) else None,
            outro=outro if outro and os.path.exists(outro) else None,
        )
        final_key = f"podcast/{episode_id}.mp3"
        storage.upload_file(out_path, final_key, content_type="audio/mpeg")

    audio_url = storage.public_url(final_key)
    with get_conn() as conn:
        # Keep an already-published episode live when re-narrated; else mark it ready for review.
        target_status = repo.episode_audio_target_status(conn, episode_id)
        repo.update_episode_audio(conn, episode_id, audio_url, int(duration), size, status=target_status)
        repo.complete_job(conn, job_id, final_key)
        repo.request_site_rebuild(conn)
        conn.commit()

    log.info("episode %s audio ready: %s (%.1fs, %d bytes)", episode_id, audio_url, duration, size)
    return {"audio_url": audio_url, "duration": int(duration), "size": size}


def drain_once(limit: int = 5) -> dict:
    """Synthesize queued narration jobs with the configured cloud provider. No-op for ``local``."""
    provider = get_provider()
    if provider is None:  # local → the home worker drains the queue
        return {}
    processed: dict[str, str] = {}
    for _ in range(limit):
        with get_conn() as conn:
            job = repo.claim_next_job(conn, "vps-narrator")
            conn.commit()
        if not job:
            break
        jid, eid = job["id"], job["episode_id"]
        try:
            ep = repo.get_episode(eid)
            language = (ep or {}).get("language") or get_settings().primary_language_code
            raw = provider.synthesize(job["text"], voice=voice_for(language), language=language)
            complete_narration(eid, jid, raw)
            processed[jid] = "ok"
        except Exception as exc:  # noqa: BLE001 — isolate; the job retries per its attempt limit
            with get_conn() as conn:
                repo.fail_job(conn, jid, str(exc)[:500])
                conn.commit()
            log.warning("narration job %s failed: %s", jid, exc)
            processed[jid] = f"failed: {exc}"
    return processed
