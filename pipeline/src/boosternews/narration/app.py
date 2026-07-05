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

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from .. import repository as repo
from ..config import get_settings
from ..db import get_conn
from .service import complete_narration

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
    # When a cloud provider is active, the VPS drainer processes jobs — serve none to the home
    # worker so a job is never synthesized twice.
    if (get_settings().narration_provider or "local").strip().lower() != "local":
        return Response(status_code=204)
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
    with get_conn() as conn:
        job = repo.get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = complete_narration(job["episode_id"], job_id, data)
    return {"ok": True, **result}


@app.post("/narration/{job_id}/fail")
def fail(job_id: str, payload: dict | None = None, _: None = Depends(require_token)):
    error = (payload or {}).get("error", "")
    with get_conn() as conn:
        status = repo.fail_job(conn, job_id, error)
        conn.commit()
    log.warning("job %s failed → %s (%s)", job_id, status, error)
    return {"status": status}
