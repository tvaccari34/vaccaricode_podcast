# sound-worker

Runs on the **home computer** (NVIDIA RTX 4060 Ti). Together with a local **VoiceStudio**
container it is the only boosternews component that runs at home. It pulls narration jobs from the
VPS, synthesizes speech in Tiago's cloned voice, and uploads the audio back — all over **outbound
HTTPS**. No inbound ports are opened; the home network needs no static IP.

## How it connects

```
home worker  ──POST /narration/claim──▶  VPS   (claim next queued job: text + language)
     │       ◀──────── job ─────────────
     │──POST /v1/audio/speech──▶ VoiceStudio (same machine, http://voicestudio:3900)
             ──POST /narration/{id}/complete (audio) ──▶  VPS
```

If the VPS is unreachable or no jobs are queued, the worker backs off and retries. If the home
PC is asleep, jobs simply wait in the VPS queue.

## Engines (`TTS_ENGINE`)

| Engine | How it synthesizes |
|--------|--------------------|
| `voicestudio` (default) | Calls [VoiceStudio](https://github.com/debpalash/voicestudio)'s OpenAI-compatible `/v1/audio/speech` with the job language's **voice profile**. Long scripts are split on paragraph/sentence boundaries (≤ `VOICESTUDIO_MAX_CHARS`), requested as raw 24 kHz PCM, and joined into one WAV. |
| `f5` | In-process F5-TTS (pt-BR fine-tune), zero-shot from `REFERENCE_SAMPLE_PATH`. |
| `xtts` | In-process coqui XTTS-v2, zero-shot from `REFERENCE_SAMPLE_PATH`. |

With `voicestudio`, the worker **doesn't claim jobs while VoiceStudio's `/health` isn't 200** (e.g.
during the first-boot model download), so jobs don't burn their retry attempts on a cold engine.
An unknown `TTS_ENGINE` stops the worker at startup.

VoiceStudio embeds an inaudible provenance watermark in generated audio. It is AGPL-3.0 and runs
unmodified as a separate container; check model-weight licenses in its Model Manager.

## Config (home `.env`)

| Var | Meaning |
|-----|---------|
| `VPS_API_URL` | Base URL of the VPS narration API (e.g. `https://tiagovaccari.com/api`) |
| `WORKER_AUTH_TOKEN` | Shared bearer token (must match the VPS) |
| `VOICE_ID` | Cloned voice id (default `tiago`) |
| `TTS_ENGINE` | `voicestudio` (default) \| `f5` \| `xtts` |
| `OMNIVOICE_API_KEY` | VoiceStudio admin/API key; compose passes it to the worker as `VOICESTUDIO_API_KEY` |
| `VOICESTUDIO_VOICE` | Voice profile id for the primary language (required for `voicestudio`) |
| `VOICESTUDIO_VOICE_EN` | Optional voice profile for `SECONDARY_LANGUAGE_CODE` (default `en`); falls back to the primary, which narrates English well with OmniVoice |
| `VOICESTUDIO_NUM_STEP` | OmniVoice quality steps per request (default 32, the model's quality preset; VoiceStudio's own default is 16) |
| `VOICESTUDIO_MODEL` | VoiceStudio engine (default `omnivoice`) |
| `VOICESTUDIO_MAX_CHARS` | Max characters per request (default 2000, must be < 4096) |
| `VOICESTUDIO_TIMEOUT_SECONDS` | Per-request synthesis timeout (default 600) |
| `REFERENCE_SAMPLE_PATH` | Private voice reference WAV for `f5` / `xtts` (mounted into the container) |

Create the VoiceStudio profiles once from the reference WAVs — see `deploy/voice/README.md`.

## Run

```bash
cd deploy
docker compose -f compose.home.yml up -d
docker compose -f compose.home.yml logs -f sound-worker
```

## Tests

```bash
pip install -e ".[dev]" && pytest
```
