"""Pluggable text-to-speech providers for podcast narration.

``local`` (default) means the home GPU sound-worker synthesizes over the job queue — there is no
server-side provider. ``elevenlabs`` and ``custom`` synthesize on the VPS via these providers.
"""

from __future__ import annotations

import re
from typing import Protocol

from ..config import get_settings


class TTSError(Exception):
    """A provider could not synthesize (missing config, API error)."""


class TTSProvider(Protocol):
    def synthesize(self, text: str, *, voice: str, language: str) -> bytes:
        """Return raw speech audio (mp3/wav) for ``text`` in the given voice/language."""
        ...


def get_provider(name: str | None = None) -> TTSProvider | None:
    """The active VPS-side provider, or None for ``local`` (the home worker handles it)."""
    s = get_settings()
    name = (name or s.narration_provider or "local").strip().lower()
    if name == "elevenlabs":
        from .elevenlabs import ElevenLabsProvider

        return ElevenLabsProvider()
    if name == "custom":
        from .custom import CustomHttpProvider

        return CustomHttpProvider()
    return None


def voice_for(language: str) -> str:
    """Resolve the configured voice id for the active provider + language."""
    s = get_settings()
    name = (s.narration_provider or "local").strip().lower()
    secondary = bool(s.secondary_language_code) and language == s.secondary_language_code
    if name == "elevenlabs":
        return s.elevenlabs_voice_id_en if secondary and s.elevenlabs_voice_id_en else s.elevenlabs_voice_id
    if name == "custom":
        return s.custom_tts_voice_en if secondary and s.custom_tts_voice_en else s.custom_tts_voice
    return s.voice_id


def chunk_text(text: str, max_chars: int = 2200) -> list[str]:
    """Split ``text`` into <= ``max_chars`` chunks on paragraph/sentence boundaries.

    Cloud TTS APIs cap the characters per request; podcast scripts exceed that, so we synthesize
    chunk-by-chunk and concatenate the audio.
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
