"""Sound-worker configuration (fail-fast).

These run on the HOME machine. The worker only needs to know how to reach the VPS narration
API and which cloned voice to use; the reference sample and model stay local.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TTS_ENGINES = ("voicestudio", "xtts", "f5")


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required: how to reach the VPS and authenticate.
    vps_api_url: str = Field(..., description="Base URL of the VPS narration API")
    worker_auth_token: str = Field(..., description="Bearer token shared with the VPS")

    # Identity + voice.
    worker_id: str = "home-4060ti"
    voice_id: str = "tiago"

    # TTS engine: "voicestudio" (default — self-hosted VoiceStudio over HTTP on the home network),
    # "xtts" (coqui XTTS-v2, in-process) or "f5" (F5-TTS, in-process).
    tts_engine: str = "voicestudio"

    # VoiceStudio (https://github.com/debpalash/voicestudio). Voices are VoiceStudio voice
    # profiles cloned from the reference sample in its UI; pass the profile id (or unique name).
    voicestudio_url: str = "http://voicestudio:3900"
    voicestudio_api_key: str = ""  # = the container's OMNIVOICE_API_KEY
    voicestudio_model: str = "omnivoice"
    voicestudio_voice: str = ""  # primary-language voice profile
    voicestudio_voice_en: str = ""  # secondary-language voice profile (falls back to the primary)
    voicestudio_max_chars: int = Field(2000, gt=0, lt=4096)  # VoiceStudio caps input at 4096
    voicestudio_timeout_seconds: int = 600
    # OmniVoice iterative-unmasking steps. VoiceStudio's API default is 16; 32 is the model's
    # documented quality preset and sounded clearly better in A/B tests at no noticeable speed cost.
    voicestudio_num_step: int = Field(32, ge=1, le=128)
    # Jobs in this language use voicestudio_voice_en (mirrors the VPS's SECONDARY_LANGUAGE_CODE).
    secondary_language_code: str = "en"

    # XTTS-v2 model + the owner's private reference sample (kept on the home machine).
    model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    reference_sample_path: str = "/data/voice/reference.wav"
    language: str = "en"

    # F5-TTS (Brazilian Portuguese). Model downloaded from HF on first run; ref auto-trimmed short.
    f5_model_repo: str = "firstpixel/F5-TTS-pt-br"
    f5_ckpt_file: str = "model_last.safetensors"
    f5_vocab_file: str = "vocab.txt"
    f5_model_arch: str = "F5TTS_Base"
    f5_ref_text: str = ""  # transcript of the reference clip; empty → auto-transcribe (ASR)
    f5_ref_max_seconds: int = 12  # trim long references (F5 prefers 5-12s clips)

    # XTTS-v2 inference tuning (override via env: TTS_TEMPERATURE, TTS_SPEED, …).
    #   temperature: lower (0.5-0.65) = steadier/less weird; higher (0.75-0.9) = more expressive.
    #   repetition_penalty: higher reduces stutters/robotic repeats.
    #   speed: 1.0 = normal; <1 slower, >1 faster.
    #   split_sentences: synthesize sentence-by-sentence (better prosody for long scripts).
    tts_temperature: float = 0.65
    tts_length_penalty: float = 1.0
    tts_repetition_penalty: float = 5.0
    tts_top_k: int = 50
    tts_top_p: float = 0.85
    tts_speed: float = 1.0
    tts_split_sentences: bool = True

    # Polling cadence + resilience.
    poll_interval_seconds: int = 10
    request_timeout_seconds: int = 120

    @field_validator("tts_engine")
    @classmethod
    def _check_engine(cls, v: str) -> str:
        name = (v or "").strip().lower()
        if name not in TTS_ENGINES:
            raise ValueError(f"TTS_ENGINE must be one of {', '.join(TTS_ENGINES)}")
        return name


@lru_cache(maxsize=1)
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()  # type: ignore[call-arg]
