"""Pull-based narration worker loop (skeleton).

The worker connects OUT to the VPS, claims the next queued narration job, synthesizes it with
the cloned voice, and uploads the resulting audio back. No inbound ports are opened on the home
network. If the VPS is unreachable or no jobs are queued, it backs off and retries.

Task group 1 provides this control loop and the HTTP contract. The actual XTTS-v2 synthesis is
implemented in task group 4 (see the ``synthesize`` TODO below).
"""

from __future__ import annotations

import logging
import re
import time
import unicodedata

import httpx

from .config import WorkerSettings, get_worker_settings

log = logging.getLogger("sound_worker")


# ── TTS text normalization ───────────────────────────────────────────────────
# F5-TTS pronounces stray symbols instead of treating them as pauses, so the LLM
# script is cleaned before synthesis: quotes/markdown are dropped, dashes and
# ellipses become sentence punctuation (a pause), and the display copy in the DB
# is left untouched. Pure + regex-only so it is easy to unit-test.
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")          # [text](url) -> text
_MD_MARKS = re.compile(r"[*_`#>~|^]")                     # emphasis / heading / code marks
_BRACKETS = re.compile(r"[\[\]{}<>]")                     # stray brackets
_DASHES = re.compile(r"\s*[—–]+\s*")                      # em/en dash -> pause
_ELLIPSIS = re.compile(r"…|\.{3,}")                       # ellipsis -> full stop
_DBL_QUOTES = {c: None for c in map(ord, "\"“”„‟«»❝❞〝〞＂")}  # drop double-quote family
_APOSTROPHES = {ord(c): "'" for c in "‘’‚‛"}              # curly apostrophes -> straight
_PARA_BREAK = re.compile(r"([^.!?:;])\s*\n+")             # unterminated line break -> add stop
_NEWLINES = re.compile(r"\s*\n+\s*")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?])")
_DUP_PUNCT = re.compile(r"([,.;:!?])(?:\s*\1)+")          # ",," / ". ." -> ","
_MULTISPACE = re.compile(r"[ \t]+")


def normalize_for_tts(text: str) -> str:
    """Strip symbols F5-TTS would read aloud, turning them into natural pauses."""
    text = unicodedata.normalize("NFKC", text)
    text = _MD_LINK.sub(r"\1", text)
    text = text.translate(_DBL_QUOTES).translate(_APOSTROPHES)
    text = _MD_MARKS.sub("", text)
    text = _BRACKETS.sub("", text)
    text = _DASHES.sub(", ", text)
    text = _ELLIPSIS.sub(".", text)
    text = text.replace("(", ", ").replace(")", ", ")
    text = _PARA_BREAK.sub(r"\1. ", text)
    text = _NEWLINES.sub(" ", text)
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    text = _DUP_PUNCT.sub(r"\1", text)
    text = _MULTISPACE.sub(" ", text)
    return text.strip()


def _client(settings: WorkerSettings) -> httpx.Client:
    return httpx.Client(
        base_url=settings.vps_api_url.rstrip("/"),
        headers={"Authorization": f"Bearer {settings.worker_auth_token}"},
        timeout=settings.request_timeout_seconds,
    )


def claim_job(client: httpx.Client, worker_id: str) -> dict | None:
    """Claim the next queued narration job, or return None if none are available."""
    resp = client.post("/narration/claim", json={"worker_id": worker_id})
    if resp.status_code == 204:  # nothing queued
        return None
    resp.raise_for_status()
    return resp.json()


def complete_job(client: httpx.Client, job_id: str, audio: bytes) -> None:
    """Upload the synthesized audio for a completed job."""
    resp = client.post(
        f"/narration/{job_id}/complete",
        files={"audio": ("narration.wav", audio, "audio/wav")},
    )
    resp.raise_for_status()


def fail_job(client: httpx.Client, job_id: str, error: str) -> None:
    """Report a synthesis failure so the VPS can requeue or give up per max_attempts."""
    resp = client.post(f"/narration/{job_id}/fail", json={"error": error})
    resp.raise_for_status()


_model = None
_f5_model = None
_f5_ref = None


def _get_model(settings: WorkerSettings):
    """Load XTTS-v2 once and cache it (GPU if available, else CPU)."""
    global _model
    if _model is None:
        import torch
        from TTS.api import TTS  # coqui-tts

        device = "cuda" if torch.cuda.is_available() else "cpu"
        log.info("loading XTTS model %s on %s", settings.model_name, device)
        _model = TTS(settings.model_name).to(device)
    return _model


def _get_f5_model(settings: WorkerSettings):
    """Load the F5-TTS (pt-BR) model once, downloading the checkpoint from HF on first use."""
    global _f5_model
    if _f5_model is None:
        import torch
        from f5_tts.api import F5TTS
        from huggingface_hub import hf_hub_download

        ckpt = hf_hub_download(settings.f5_model_repo, settings.f5_ckpt_file)
        vocab = ""
        if settings.f5_vocab_file:
            try:
                vocab = hf_hub_download(settings.f5_model_repo, settings.f5_vocab_file)
            except Exception as exc:  # noqa: BLE001 — fall back to the base vocab
                log.warning("no vocab file %s in repo (%s); using default", settings.f5_vocab_file, exc)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        log.info("loading F5-TTS %s (%s) on %s", settings.f5_model_repo, settings.f5_model_arch, device)
        _f5_model = F5TTS(
            model=settings.f5_model_arch, ckpt_file=ckpt, vocab_file=vocab, device=device
        )
    return _f5_model


def _f5_reference(settings: WorkerSettings) -> str:
    """Trim the reference clip to a short mono 24kHz WAV (F5 prefers 5-12s references)."""
    global _f5_ref
    if _f5_ref is None:
        import subprocess
        import tempfile

        out = tempfile.mktemp(suffix="_f5ref.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", settings.reference_sample_path, "-t",
             str(settings.f5_ref_max_seconds), "-ac", "1", "-ar", "24000", out],
            check=True,
            capture_output=True,
        )
        _f5_ref = out
    return _f5_ref


def _synthesize_f5(text: str, settings: WorkerSettings, out_path: str) -> None:
    model = _get_f5_model(settings)
    model.infer(
        ref_file=_f5_reference(settings),
        ref_text=settings.f5_ref_text,  # empty → F5 auto-transcribes the reference
        gen_text=text,
        file_wave=out_path,
        speed=settings.tts_speed,
        remove_silence=True,
    )


def _synthesize_xtts(text: str, settings: WorkerSettings, out_path: str) -> None:
    _get_model(settings).tts_to_file(
        text=text,
        speaker_wav=settings.reference_sample_path,
        language=settings.language,
        file_path=out_path,
        split_sentences=settings.tts_split_sentences,
        temperature=settings.tts_temperature,
        length_penalty=settings.tts_length_penalty,
        repetition_penalty=settings.tts_repetition_penalty,
        top_k=settings.tts_top_k,
        top_p=settings.tts_top_p,
        speed=settings.tts_speed,
    )


def synthesize(text: str, settings: WorkerSettings) -> bytes:
    """Render ``text`` to speech in the owner's cloned voice. Returns WAV bytes.

    Zero-shot voice cloning from the reference sample via the configured engine (xtts | f5).
    Requires a registered reference sample — fails loudly rather than using a different voice.
    """
    import os
    import tempfile

    text = normalize_for_tts(text)

    if not settings.reference_sample_path or not os.path.exists(settings.reference_sample_path):
        raise FileNotFoundError(
            f"voice reference sample not found at {settings.reference_sample_path!r}; "
            "record a short clean WAV of the owner's voice and mount it there"
        )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
        out_path = fh.name
    try:
        if settings.tts_engine == "f5":
            _synthesize_f5(text, settings, out_path)
        else:
            _synthesize_xtts(text, settings, out_path)
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_worker_settings()
    log.info(
        "sound-worker '%s' starting; VPS=%s voice=%s",
        settings.worker_id,
        settings.vps_api_url,
        settings.voice_id,
    )

    with _client(settings) as client:
        while True:
            try:
                job = claim_job(client, settings.worker_id)
            except httpx.HTTPError as exc:
                log.warning("could not reach VPS (%s); backing off", exc)
                time.sleep(settings.poll_interval_seconds)
                continue

            if job is None:
                time.sleep(settings.poll_interval_seconds)
                continue

            job_id = job["id"]
            log.info("claimed job %s (episode %s)", job_id, job.get("episode_id"))
            try:
                audio = synthesize(job["text"], settings)
                complete_job(client, job_id, audio)
                log.info("completed job %s", job_id)
            except Exception as exc:  # noqa: BLE001 — report and keep the loop alive
                log.exception("job %s failed", job_id)
                try:
                    fail_job(client, job_id, str(exc))
                except httpx.HTTPError:
                    log.warning("could not report failure for job %s", job_id)
