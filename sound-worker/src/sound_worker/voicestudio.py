"""VoiceStudio engine: synthesize narration through a self-hosted VoiceStudio over HTTP.

VoiceStudio (https://github.com/debpalash/voicestudio) runs as its own container next to the
worker on the home network and owns the GPU; the worker only talks to its OpenAI-compatible
``POST /v1/audio/speech`` endpoint and ``GET /health``. Podcast scripts exceed VoiceStudio's
4096-char input cap, so each chunk is requested as raw PCM (24 kHz, s16le, mono) — which
concatenates cleanly, unlike WAV/MP3 containers — and the whole script is wrapped in one WAV.
"""

from __future__ import annotations

import io
import re
import wave

import httpx

from .config import WorkerSettings

# VoiceStudio's `pcm` response_format: raw 24 kHz 16-bit little-endian mono.
SAMPLE_RATE = 24000
SAMPLE_WIDTH = 2
CHANNELS = 1


class VoiceStudioError(Exception):
    """VoiceStudio could not synthesize (missing voice profile, API error, timeout)."""


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Split ``text`` into <= ``max_chars`` chunks on paragraph/sentence boundaries.

    Ported from the pipeline's ``boosternews.tts.chunk_text`` (the worker doesn't depend on it).
    """
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    parts = re.split(r"(\n\n+|(?<=[.!?])\s+)", text)
    chunks: list[str] = []
    cur = ""
    for p in parts:
        if not p:
            continue
        if len(cur) + len(p) > max_chars and cur:
            chunks.append(cur.strip())
            cur = ""
        cur += p
    if cur.strip():
        chunks.append(cur.strip())
    # Hard-wrap anything still over the limit (e.g. one giant sentence).
    out: list[str] = []
    for c in chunks:
        while len(c) > max_chars:
            out.append(c[:max_chars])
            c = c[max_chars:]
        if c.strip():
            out.append(c)
    return out


def iso639_1(code: str) -> str:
    """Reduce a language tag to its ISO 639-1 base subtag (``pt-BR`` → ``pt``)."""
    return re.split(r"[-_]", (code or "").strip(), maxsplit=1)[0].lower()


def voice_for(language: str | None, settings: WorkerSettings) -> str:
    """The VoiceStudio voice profile for ``language``. Never falls back to an engine default."""
    secondary = bool(language and settings.secondary_language_code) and iso639_1(
        language
    ) == iso639_1(settings.secondary_language_code)
    if secondary and settings.voicestudio_voice_en:
        return settings.voicestudio_voice_en
    if not settings.voicestudio_voice:
        hint = " (or VOICESTUDIO_VOICE_EN for this language)" if secondary else ""
        raise VoiceStudioError(
            f"no VoiceStudio voice profile configured: set VOICESTUDIO_VOICE{hint}"
        )
    return settings.voicestudio_voice


def client(settings: WorkerSettings) -> httpx.Client:
    headers = {}
    if settings.voicestudio_api_key:
        headers["Authorization"] = f"Bearer {settings.voicestudio_api_key}"
    return httpx.Client(
        base_url=settings.voicestudio_url.rstrip("/"),
        headers=headers,
        timeout=settings.voicestudio_timeout_seconds,
    )


def health_ok(vs: httpx.Client) -> bool:
    """True once VoiceStudio is ready (``/health`` is 503 while models download/load)."""
    try:
        return vs.get("/health").status_code == 200
    except httpx.HTTPError:
        return False


def pcm_to_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(SAMPLE_WIDTH)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    return buf.getvalue()


def _error_message(resp: httpx.Response) -> str:
    """VoiceStudio errors use OpenAI's shape: {"error": {"message": ...}}."""
    try:
        return str(resp.json()["error"]["message"])
    except Exception:  # noqa: BLE001 — not JSON / unexpected shape
        return resp.text[:300]


def synthesize(
    text: str,
    language: str | None,
    settings: WorkerSettings,
    vs: httpx.Client | None = None,
) -> bytes:
    """Render already-normalized ``text`` in the language's cloned voice. Returns WAV bytes.

    ``language`` is the job's language; None (a VPS predating it) means ``settings.language``
    with the primary voice.
    """
    voice = voice_for(language, settings)
    chunks = chunk_text(text, settings.voicestudio_max_chars)
    if not chunks:
        raise VoiceStudioError("nothing to synthesize (empty text)")
    if vs is None:
        with client(settings) as owned:
            return synthesize(text, language, settings, owned)

    lang = iso639_1(language or settings.language)
    pcm = bytearray()
    for i, chunk in enumerate(chunks, 1):
        try:
            resp = vs.post(
                "/v1/audio/speech",
                json={
                    "model": settings.voicestudio_model,
                    "input": chunk,
                    "voice": voice,
                    "language": lang,
                    "response_format": "pcm",
                    "speed": settings.tts_speed,
                    "num_step": settings.voicestudio_num_step,
                },
            )
        except httpx.TimeoutException as exc:
            raise VoiceStudioError(
                f"VoiceStudio timed out after {settings.voicestudio_timeout_seconds}s "
                f"on chunk {i}/{len(chunks)}"
            ) from exc
        if resp.status_code != 200:
            raise VoiceStudioError(f"VoiceStudio {resp.status_code}: {_error_message(resp)}")
        pcm.extend(resp.content)
    return pcm_to_wav(bytes(pcm))
