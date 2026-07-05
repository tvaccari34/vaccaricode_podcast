"""Central configuration with fail-fast validation.

Required settings have no default: if any is missing at startup the process raises a clear
``pydantic.ValidationError`` listing exactly which environment variables are absent, rather
than starting in a half-configured state.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Required secrets / connections (no defaults → fail fast) ──────────
    database_url: str = Field(..., description="PostgreSQL DSN for the app database")
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    s3_endpoint_url: str = Field(..., description="S3-compatible endpoint (e.g. MinIO)")
    s3_access_key_id: str = Field(...)
    s3_secret_access_key: str = Field(...)
    worker_auth_token: str = Field(..., description="Bearer token the home sound-worker uses")

    # ── Optional / defaulted ─────────────────────────────────────────────
    gemini_model: str = "gemini-2.5-flash"
    s3_region: str = "us-east-1"
    s3_bucket_audio: str = "boosternews-audio"
    s3_public_base_url: str = ""
    site_domain: str = "tiagovaccari.com"
    # Optional GitHub token raises the Search API rate limit for trend discovery.
    github_token: str = ""
    # Review dashboard HTTP Basic Auth. If dashboard_password is empty, auth is DISABLED (dev only
    # — a warning is logged). Set a password to require login on every dashboard route.
    dashboard_user: str = "admin"
    dashboard_password: str = ""
    # Content generation: author identity + optional brand-voice override.
    author_name: str = "Tiago Vaccari"
    brand_voice: str = ""
    # Language of generated content (blog/newsletter/podcast). e.g. "Brazilian Portuguese", "English".
    content_language: str = "Brazilian Portuguese"
    # Heading used for the auto-appended sources section (localized).
    sources_heading: str = "Fontes"
    # Fixed spoken intro prepended to every podcast script (the model is told not to add its own).
    podcast_intro: str = (
        "Fala galera! Bem vindo novamente ao Vaccari's Code Podcast. Tiago Vaccari aqui."
    )
    primary_language_code: str = "pt-BR"
    # Secondary language mirror (blog + newsletter + podcast SCRIPT; audio uploaded manually, not
    # auto-narrated). Set secondary_language="" to disable the English version entirely.
    secondary_language: str = "English"
    secondary_language_code: str = "en"
    secondary_sources_heading: str = "Sources"
    podcast_intro_en: str = (
        "What's up everyone! Welcome back to Vaccari's Code Podcast. Tiago here."
    )
    # Subscribe CTA: a referral block appended to generated blog posts + episode show notes,
    # pointing readers/listeners at the newsletter. Disable with subscribe_cta_enabled=false.
    # {url} is filled with the language's subscribe page under public_site_url (so set that to the
    # real domain in prod — it doubles as the permalink base below).
    subscribe_cta_enabled: bool = True
    subscribe_path: str = "/subscribe"
    subscribe_cta: str = (
        "📬 **Gostou?** Assine a newsletter do Vaccari's Code e receba as próximas tendências "
        "em software e IA direto no seu e-mail: **[Assinar aqui]({url})**"
    )
    subscribe_cta_en: str = (
        "📬 **Enjoyed this?** Subscribe to the Vaccari's Code newsletter for the next wave of "
        "software & AI trends, straight to your inbox: **[Subscribe here]({url})**"
    )
    # Publishing: public base URL for permalinks + Listmonk campaign API (optional until group 7).
    public_site_url: str = "http://localhost"
    listmonk_api_url: str = "http://listmonk:9000"
    listmonk_api_user: str = ""
    listmonk_api_token: str = ""
    listmonk_list_id: int = 0  # primary-language (pt-BR) list
    listmonk_list_id_en: int = 0  # secondary-language (English) list
    # Scheduler (task group 9). Minutes per job; 0 disables. tick = poll granularity.
    sched_tick_seconds: int = 30
    sched_ingest_minutes: int = 60
    sched_extract_minutes: int = 30
    sched_generate_minutes: int = 0  # 0 = don't auto-generate (controls LLM spend)
    sched_publish_minutes: int = 15
    sched_max_cycles: int = 0  # 0 = run forever; >0 bounds the loop (tests/one-shot)
    # Podcast production (task group 4): default cloned voice + optional intro/outro audio.
    voice_id: str = "tiago"
    audio_intro_path: str = ""
    audio_outro_path: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings. Raises on missing required values."""
    return Settings()  # type: ignore[call-arg]


def mask(value: str, keep: int = 4) -> str:
    """Mask a secret for safe display in logs."""
    if not value:
        return "<empty>"
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "…" + "*" * 4
