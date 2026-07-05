"""ElevenLabs text-to-speech provider (managed voice cloning)."""

from __future__ import annotations

import logging

import httpx

from ..config import get_settings
from . import TTSError, chunk_text

log = logging.getLogger("boosternews.tts.elevenlabs")

API = "https://api.elevenlabs.io/v1/text-to-speech"


class ElevenLabsProvider:
    def synthesize(self, text: str, *, voice: str, language: str) -> bytes:
        s = get_settings()
        if not s.elevenlabs_api_key:
            raise TTSError("ELEVENLABS_API_KEY is not set")
        if not voice:
            raise TTSError("no ElevenLabs voice id configured for this language")
        headers = {
            "xi-api-key": s.elevenlabs_api_key,
            "accept": "audio/mpeg",
            "content-type": "application/json",
        }
        out = bytearray()
        for chunk in chunk_text(text, 2200):
            resp = httpx.post(
                f"{API}/{voice}",
                headers=headers,
                json={
                    "text": chunk,
                    "model_id": s.elevenlabs_model,
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                timeout=300,
            )
            if resp.status_code != 200:
                raise TTSError(f"ElevenLabs {resp.status_code}: {resp.text[:300]}")
            out.extend(resp.content)
        if not out:
            raise TTSError("nothing to synthesize (empty text)")
        return bytes(out)
