"""FastAPI review dashboard.

Runs on the VPS (private). Shows pending drafts per topic and language — blog text, newsletter
blurb, and a podcast audio preview (or script) — and records per-channel approve / request-edit /
reject decisions. Approval is the gate before publishing.

For secondary-language (English) episodes there is no auto-narration: the reviewer downloads the
script, records the audio manually, and uploads the MP3 here — which stores it and marks the
episode ready.
"""

from __future__ import annotations

import logging
import os
import secrets
import tempfile

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jinja2 import DictLoader, Environment, select_autoescape

from .. import audio
from .. import repository as repo
from .. import storage
from ..config import get_settings
from ..db import get_conn
from .templates import TEMPLATES

log = logging.getLogger("boosternews.dashboard")
_env = Environment(loader=DictLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
_security = HTTPBasic(auto_error=False)

app = FastAPI(title="boosternews review dashboard")


def require_auth(credentials: HTTPBasicCredentials | None = Depends(_security)) -> None:
    """HTTP Basic Auth guard. Disabled (with a warning) if no dashboard password is configured."""
    s = get_settings()
    if not s.dashboard_password:
        log.warning("dashboard auth DISABLED (no DASHBOARD_PASSWORD set) — do not expose publicly")
        return
    ok = (
        credentials is not None
        and secrets.compare_digest(credentials.username, s.dashboard_user)
        and secrets.compare_digest(credentials.password, s.dashboard_password)
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/", response_class=HTMLResponse)
def index(_auth: None = Depends(require_auth)) -> HTMLResponse:
    s = get_settings()
    queue = repo.get_review_queue()
    manual = repo.list_secondary_episodes()
    episodes = repo.list_primary_episodes()
    html = _env.get_template("index.html").render(
        queue=queue,
        reviewer=s.author_name,
        primary=s.primary_language_code,
        manual=manual,
        episodes=episodes,
    )
    return HTMLResponse(html)


@app.post("/review")
def review(
    topic_id: str = Form(...),
    channel: str = Form(...),
    decision: str = Form(...),
    reviewer: str = Form("reviewer"),
    notes: str = Form(""),
    language: str = Form("pt-BR"),
    _auth: None = Depends(require_auth),
) -> RedirectResponse:
    with get_conn() as conn:
        repo.record_review(
            conn,
            topic_id=topic_id,
            channel=channel,
            decision=decision,
            reviewer=reviewer,
            notes=notes or None,
            language=language,
        )
        conn.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/episode/{episode_id}/script", response_class=PlainTextResponse)
def download_script(episode_id: str, _auth: None = Depends(require_auth)) -> PlainTextResponse:
    """Download the episode narration script as plain text (to record the audio)."""
    ep = repo.get_episode(episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="episode not found")
    filename = f"{ep['language']}-{episode_id[:8]}.txt"
    return PlainTextResponse(
        ep["script"], headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.post("/episode/{episode_id}/renarrate")
def renarrate(
    episode_id: str,
    script: str = Form(...),
    _auth: None = Depends(require_auth),
) -> RedirectResponse:
    """Save an edited narration script and queue a fresh auto-narration job (pt-BR sound-worker).

    Clears the episode's old audio and enqueues a new job; the home GPU worker picks it up on its
    next poll and regenerates the MP3 in the cloned voice.
    """
    ep = repo.get_episode(episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="episode not found")
    if not script.strip():
        raise HTTPException(status_code=400, detail="script cannot be empty")
    with get_conn() as conn:
        job_id = repo.update_script_and_renarrate(conn, episode_id, script)
        conn.commit()
    log.info("episode %s script edited; queued narration job %s", episode_id, job_id)
    return RedirectResponse("/", status_code=303)


@app.post("/episode/{episode_id}/audio")
async def upload_audio(
    episode_id: str,
    audio_file: UploadFile = File(..., alias="audio"),
    _auth: None = Depends(require_auth),
):
    """Manually upload recorded audio for an episode (e.g. the English version)."""
    ep = repo.get_episode(episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="episode not found")
    data = await audio_file.read()

    storage.ensure_bucket()
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "upload")
        out = os.path.join(tmp, "episode.mp3")
        with open(src, "wb") as fh:
            fh.write(data)
        duration, size = audio.assemble(src, out)  # normalize + encode to mp3
        key = f"podcast/{episode_id}.mp3"
        storage.upload_file(out, key, content_type="audio/mpeg")

    audio_url = storage.public_url(key)
    with get_conn() as conn:
        repo.update_episode_audio(conn, episode_id, audio_url, int(duration), size, status="ready")
        conn.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health() -> dict:
    return {"ok": True}
