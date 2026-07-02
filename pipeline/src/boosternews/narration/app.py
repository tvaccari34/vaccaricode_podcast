"""Narration job API (FastAPI), token-authenticated, served on the VPS.

The home GPU sound-worker calls these over outbound HTTPS:
  POST /narration/claim               → claim the next queued job (or 204)
  POST /narration/{job_id}/complete   → upload synthesized audio → assemble → publish to storage
  POST /narration/{job_id}/fail       → report failure (requeue or fail per attempts)

On completion the VPS assembles the raw narration (intro/outro + loudness normalization + MP3),
uploads it to object storage, and records the audio URL + duration + size on the episode.
"""

from __future__ import annotations

import logging
import os
import tempfile

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from .. import audio
from .. import repository as repo
from .. import storage
from ..config import get_settings
from ..db import get_conn

log = logging.getLogger("boosternews.narration")

app = FastAPI(title="boosternews narration API")


def require_token(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {get_settings().worker_auth_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid worker token")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/narration/claim")
def claim(payload: dict | None = None, _: None = Depends(require_token)):
    worker_id = (payload or {}).get("worker_id", "worker")
    with get_conn() as conn:
        job = repo.claim_next_job(conn, worker_id)
        conn.commit()
    if not job:
        return Response(status_code=204)
    log.info("job %s claimed by %s", job["id"], worker_id)
    return JSONResponse(job)


@app.post("/narration/{job_id}/complete")
async def complete(
    job_id: str,
    audio_file: UploadFile = File(..., alias="audio"),
    _: None = Depends(require_token),
):
    data = await audio_file.read()
    settings = get_settings()

    with get_conn() as conn:
        job = repo.get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    episode_id = job["episode_id"]

    # Store the raw narration, then assemble the final episode audio.
    storage.ensure_bucket()
    storage.upload_bytes(data, f"narration/{episode_id}/raw.wav", content_type="audio/wav")

    intro = settings.audio_intro_path or None
    outro = settings.audio_outro_path or None
    with tempfile.TemporaryDirectory() as tmp:
        raw_path = os.path.join(tmp, "raw.wav")
        out_path = os.path.join(tmp, "episode.mp3")
        with open(raw_path, "wb") as fh:
            fh.write(data)
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
        # Keep an already-published episode live when it is re-narrated; otherwise mark it ready
        # for review/publish (first narration).
        target_status = repo.episode_audio_target_status(conn, episode_id)
        repo.update_episode_audio(
            conn, episode_id, audio_url, int(duration), size, status=target_status
        )
        repo.complete_job(conn, job_id, final_key)
        conn.commit()

    log.info(
        "episode %s audio ready: %s (%.1fs, %d bytes)",
        episode_id,
        audio_url,
        duration,
        size,
    )
    return {"ok": True, "audio_url": audio_url, "duration": int(duration), "size": size}


@app.post("/narration/{job_id}/fail")
def fail(job_id: str, payload: dict | None = None, _: None = Depends(require_token)):
    error = (payload or {}).get("error", "")
    with get_conn() as conn:
        status = repo.fail_job(conn, job_id, error)
        conn.commit()
    log.warning("job %s failed → %s (%s)", job_id, status, error)
    return {"status": status}
