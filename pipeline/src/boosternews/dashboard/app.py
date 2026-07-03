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


def _lang_fields() -> list[dict]:
    """Form sections for the create pages: primary language, plus secondary if enabled."""
    s = get_settings()
    fields = [{"label": f"Primary ({s.primary_language_code})", "prefix": "primary"}]
    if s.secondary_language_code:
        fields.append({"label": f"Secondary ({s.secondary_language_code})", "prefix": "secondary"})
    return fields


@app.get("/create/post", response_class=HTMLResponse)
def create_post_form(_auth: None = Depends(require_auth)) -> HTMLResponse:
    return HTMLResponse(_env.get_template("create_post.html").render(langs=_lang_fields()))


@app.post("/create/post")
def create_post(
    primary_title: str = Form(""),
    primary_body: str = Form(""),
    primary_newsletter: str = Form(""),
    secondary_title: str = Form(""),
    secondary_body: str = Form(""),
    secondary_newsletter: str = Form(""),
    action: str = Form("draft"),
    _auth: None = Depends(require_auth),
) -> RedirectResponse:
    """Create a hand-written blog post (and optional newsletter blurb) in one or both languages."""
    s = get_settings()
    rows = [
        (s.primary_language_code, primary_title, primary_body, primary_newsletter),
        (s.secondary_language_code, secondary_title, secondary_body, secondary_newsletter),
    ]
    chosen = [(lang, t.strip(), b.strip(), n.strip()) for lang, t, b, n in rows if lang and t.strip() and b.strip()]
    if not chosen:
        raise HTTPException(status_code=400, detail="provide a title and body for at least one language")
    approve = action == "approve"
    with get_conn() as conn:
        topic_id = repo.create_manual_topic(conn, chosen[0][1])
        for lang, title, body, newsletter in chosen:
            repo.upsert_draft(conn, topic_id, "blog", title, body, {}, language=lang)
            if newsletter:
                repo.upsert_draft(conn, topic_id, "newsletter", title, newsletter, {}, language=lang)
            if approve:
                repo.record_review(conn, topic_id=topic_id, channel="blog", decision="approve", reviewer=s.author_name, language=lang)
                if newsletter:
                    repo.record_review(conn, topic_id=topic_id, channel="newsletter", decision="approve", reviewer=s.author_name, language=lang)
        conn.commit()
    log.info("manual post created (topic %s, %d language(s), approve=%s)", topic_id, len(chosen), approve)
    return RedirectResponse("/", status_code=303)


@app.get("/create/episode", response_class=HTMLResponse)
def create_episode_form(_auth: None = Depends(require_auth)) -> HTMLResponse:
    return HTMLResponse(
        _env.get_template("create_episode.html").render(
            langs=_lang_fields(), primary=get_settings().primary_language_code
        )
    )


@app.post("/create/episode")
def create_episode(
    primary_title: str = Form(""),
    primary_script: str = Form(""),
    primary_notes: str = Form(""),
    primary_narrate: str = Form(""),
    secondary_title: str = Form(""),
    secondary_script: str = Form(""),
    secondary_notes: str = Form(""),
    action: str = Form("draft"),
    _auth: None = Depends(require_auth),
) -> RedirectResponse:
    """Create a hand-written podcast episode in one or both languages, optionally queuing pt-BR audio."""
    s = get_settings()
    rows = [
        (s.primary_language_code, primary_title, primary_script, primary_notes, bool(primary_narrate)),
        (s.secondary_language_code, secondary_title, secondary_script, secondary_notes, False),
    ]
    chosen = [
        (lang, t.strip(), sc.strip(), n.strip(), narr)
        for lang, t, sc, n, narr in rows
        if lang and t.strip() and sc.strip()
    ]
    if not chosen:
        raise HTTPException(status_code=400, detail="provide a title and script for at least one language")
    approve = action == "approve"
    with get_conn() as conn:
        topic_id = repo.create_manual_topic(conn, chosen[0][1])
        for lang, title, script, notes, narrate in chosen:
            draft_id = repo.upsert_draft(conn, topic_id, "podcast", title, script, {}, language=lang)
            voice = s.voice_id if lang == s.primary_language_code else None
            episode_id = repo.upsert_episode(
                conn, topic_id, draft_id, title, script, notes, language=lang, voice_id=voice
            )
            if approve:
                repo.record_review(conn, topic_id=topic_id, channel="podcast", decision="approve", reviewer=s.author_name, language=lang)
            if narrate and lang == s.primary_language_code:
                repo.enqueue_narration(conn, episode_id, voice or "tiago", script)
        conn.commit()
    log.info("manual episode created (topic %s, %d language(s), approve=%s)", topic_id, len(chosen), approve)
    return RedirectResponse("/", status_code=303)


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
