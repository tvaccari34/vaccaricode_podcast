"""LLM client — Google Gemini (google-genai SDK).

A thin provider wrapper so the rest of the pipeline depends on ``generate(...)`` rather than a
specific SDK. Content generation (task group 3) calls this to turn a topic + its extracted
source text into a blog post, podcast script, and newsletter blurb.

Swapping providers later means changing only this module.
"""

from __future__ import annotations

from functools import lru_cache

from google import genai
from google.genai import types

from .config import get_settings


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Return a cached Gemini client built from the configured API key."""
    return genai.Client(api_key=get_settings().gemini_api_key)


def generate(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_output_tokens: int | None = None,
) -> str:
    """Generate text from a prompt and return the model's response text.

    ``system`` sets the system instruction (brand voice / format rules); ``model`` overrides the
    configured default (``gemini-2.5-flash``).
    """
    settings = get_settings()
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system,
        max_output_tokens=max_output_tokens,
    )
    response = get_client().models.generate_content(
        model=model or settings.gemini_model,
        contents=prompt,
        config=config,
    )
    return response.text or ""
