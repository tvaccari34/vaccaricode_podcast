"""Custom HTTP text-to-speech provider — your own / self-hosted voice model.

Two request shapes:
  - generic (default): POST {text, voice, language, format} to CUSTOM_TTS_URL
  - openai: POST {model, input, voice, response_format} (OpenAI-compatible /v1/audio/speech)
Both expect the response body to be the audio bytes.
"""

from __future__ import annotations

import logging

import httpx

from ..config import get_settings
from . import TTSError, chunk_text

log = logging.getLogger("boosternews.tts.custom")


class CustomHttpProvider:
    def synthesize(self, text: str, *, voice: str, language: str) -> bytes:
        s = get_settings()
        if not s.custom_tts_url:
            raise TTSError("CUSTOM_TTS_URL is not set")
        headers = {"content-type": "application/json"}
        if s.custom_tts_api_key:
            headers["Authorization"] = f"Bearer {s.custom_tts_api_key}"
        openai_mode = (s.custom_tts_format or "generic").strip().lower() == "openai"

        out = bytearray()
        for chunk in chunk_text(text, 3500):
            if openai_mode:
                body = {
                    "model": s.custom_tts_model or "tts-1",
                    "input": chunk,
                    "voice": voice or "alloy",
                    "response_format": "mp3",
                }
            else:
                body = {"text": chunk, "voice": voice, "language": language, "format": "mp3"}
            resp = httpx.post(s.custom_tts_url, headers=headers, json=body, timeout=300)
            if resp.status_code != 200:
                raise TTSError(f"custom TTS {resp.status_code}: {resp.text[:300]}")
            out.extend(resp.content)
        if not out:
            raise TTSError("nothing to synthesize (empty text)")
        return bytes(out)
