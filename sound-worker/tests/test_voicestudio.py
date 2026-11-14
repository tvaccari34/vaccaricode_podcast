"""VoiceStudio engine: request contract, voice selection, chunking + WAV assembly, errors."""

from __future__ import annotations

import io
import json
import wave

import httpx
import pytest
from pydantic import ValidationError

from sound_worker import voicestudio
from sound_worker.config import WorkerSettings
from sound_worker.worker import normalize_for_tts, synthesize

PCM_PER_CHUNK = b"\x01\x00" * 2400  # 0.1 s of 24 kHz s16le mono


def make_settings(**overrides) -> WorkerSettings:
    base = {
        "vps_api_url": "https://vps.example/api",
        "worker_auth_token": "token",
        "voicestudio_url": "http://voicestudio:3900",
        "voicestudio_voice": "owner-pt",
    }
    base.update(overrides)
    return WorkerSettings(_env_file=None, **base)


class Recorder:
    """httpx MockTransport handler that records requests and answers with PCM (or an error)."""

    def __init__(self, status: int = 200, body: bytes | None = None):
        self.status = status
        self.body = body
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/health":
            return httpx.Response(self.status)
        if self.status != 200:
            return httpx.Response(self.status, content=self.body or b"")
        return httpx.Response(200, content=PCM_PER_CHUNK)

    @property
    def bodies(self) -> list[dict]:
        return [json.loads(r.content) for r in self.requests]


def mock_client(settings: WorkerSettings, rec: Recorder) -> httpx.Client:
    vs = voicestudio.client(settings)
    vs._transport = httpx.MockTransport(rec)
    return vs


def test_request_body_and_bearer_header():
    s = make_settings(voicestudio_api_key="abc")
    rec = Recorder()
    voicestudio.synthesize("Olá, mundo.", "pt-BR", s, mock_client(s, rec))
    (req,) = rec.requests
    assert req.method == "POST" and req.url.path == "/v1/audio/speech"
    assert req.headers["authorization"] == "Bearer abc"
    assert rec.bodies[0] == {
        "model": "omnivoice",
        "input": "Olá, mundo.",
        "voice": "owner-pt",
        "language": "pt",
        "response_format": "pcm",
        "speed": 1.0,
        "num_step": 32,
    }


def test_num_step_is_configurable_and_bounded():
    s = make_settings(voicestudio_num_step=16)
    rec = Recorder()
    voicestudio.synthesize("Oi.", "pt-BR", s, mock_client(s, rec))
    assert rec.bodies[0]["num_step"] == 16
    with pytest.raises(ValueError):
        make_settings(voicestudio_num_step=0)


def test_no_auth_header_without_key():
    s = make_settings()
    rec = Recorder()
    voicestudio.synthesize("Hi.", "pt-BR", s, mock_client(s, rec))
    assert "authorization" not in rec.requests[0].headers


@pytest.mark.parametrize(
    ("language", "voice_en", "expected_voice", "expected_lang"),
    [
        ("en", "owner-en", "owner-en", "en"),
        ("en-US", "owner-en", "owner-en", "en"),
        ("en", "", "owner-pt", "en"),  # secondary falls back to the primary profile
        ("pt-BR", "owner-en", "owner-pt", "pt"),
        (None, "owner-en", "owner-pt", "en"),  # old VPS: no language → LANGUAGE (default "en")
    ],
)
def test_voice_and_language_selection(language, voice_en, expected_voice, expected_lang):
    s = make_settings(voicestudio_voice_en=voice_en)
    rec = Recorder()
    voicestudio.synthesize("Hello.", language, s, mock_client(s, rec))
    assert rec.bodies[0]["voice"] == expected_voice
    assert rec.bodies[0]["language"] == expected_lang


def test_missing_profile_fails_without_request():
    s = make_settings(voicestudio_voice="")
    rec = Recorder()
    with pytest.raises(voicestudio.VoiceStudioError, match="VOICESTUDIO_VOICE"):
        voicestudio.synthesize("Olá.", "pt-BR", s, mock_client(s, rec))
    assert rec.requests == []


def test_long_script_is_chunked_into_one_wav():
    s = make_settings()
    sentence = "Esta é uma frase de teste para o podcast. "  # 42 chars
    text = (sentence * 215).strip()  # ~9k chars
    rec = Recorder()
    wav = voicestudio.synthesize(text, "pt-BR", s, mock_client(s, rec))

    inputs = [b["input"] for b in rec.bodies]
    assert len(inputs) >= 5
    assert all(len(i) <= 2000 for i in inputs)
    assert all(i.endswith(".") for i in inputs)  # never splits a sentence that fits
    with wave.open(io.BytesIO(wav)) as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (24000, 1, 2)
        assert w.getnframes() * 2 == len(PCM_PER_CHUNK) * len(inputs)


def test_error_status_surfaces_message():
    s = make_settings()
    body = json.dumps({"error": {"message": "Unknown voice 'x'", "type": "invalid_request_error"}})
    rec = Recorder(status=400, body=body.encode())
    with pytest.raises(voicestudio.VoiceStudioError, match=r"400: Unknown voice 'x'"):
        voicestudio.synthesize("Olá.", "pt-BR", s, mock_client(s, rec))


def test_timeout_fails_with_clear_error():
    s = make_settings(voicestudio_timeout_seconds=5)

    def boom(request):
        raise httpx.ReadTimeout("timed out", request=request)

    vs = voicestudio.client(s)
    vs._transport = httpx.MockTransport(boom)
    with pytest.raises(voicestudio.VoiceStudioError, match=r"timed out after 5s on chunk 1/1"):
        voicestudio.synthesize("Olá.", "pt-BR", s, vs)


@pytest.mark.parametrize(("status", "ok"), [(200, True), (503, False)])
def test_health(status, ok):
    s = make_settings()
    assert voicestudio.health_ok(mock_client(s, Recorder(status=status))) is ok


def test_health_unreachable_is_not_ready():
    s = make_settings()

    def down(request):
        raise httpx.ConnectError("refused", request=request)

    vs = voicestudio.client(s)
    vs._transport = httpx.MockTransport(down)
    assert voicestudio.health_ok(vs) is False


def test_worker_dispatches_to_voicestudio_with_normalized_text():
    s = make_settings()
    rec = Recorder()
    synthesize("**Olá** — mundo…", s, language="pt-BR", vs=mock_client(s, rec))
    assert rec.bodies[0]["input"] == normalize_for_tts("**Olá** — mundo…") == "Olá, mundo."


def test_default_engine_is_voicestudio():
    assert make_settings().tts_engine == "voicestudio"


def test_unknown_engine_fails_fast():
    with pytest.raises(ValidationError, match="voicestudio, xtts, f5"):
        make_settings(tts_engine="elevenlabs")
