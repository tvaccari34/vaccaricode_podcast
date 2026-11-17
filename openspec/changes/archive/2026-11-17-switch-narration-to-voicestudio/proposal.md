## Why

Podcast narration is currently produced by ElevenLabs on the VPS. ElevenLabs is a paid cloud service billed per character, and it requires the owner's cloned voice to live on a third-party platform. [VoiceStudio](https://github.com/debpalash/voicestudio) is a self-hosted, local-first voice studio (AGPL-3.0, default engine OmniVoice) with voice cloning and an OpenAI-compatible `/v1/audio/speech` API. Running it on the existing home GPU box removes the per-character cost, keeps the voice reference sample at home, and fits the outbound-only home-worker architecture the project already has.

## What Changes

- Add a **VoiceStudio engine** to the home sound-worker (`TTS_ENGINE=voicestudio`, the new default). The worker calls a VoiceStudio container on the home machine over the local Docker network, in the configured cloned-voice profile, and uploads the result to the VPS exactly as today.
- Add a `voicestudio` service to the home compose stack (GPU, persistent data volume, API key, analytics disabled, health check). The sound-worker waits for it to be healthy before claiming jobs.
- Make narration **language-aware on the home worker**. The `/narration/claim` response includes the episode's `language`, and the worker picks the matching VoiceStudio voice profile and language code. This lets the home worker narrate the secondary language (English) as well, so `NARRATION_SECONDARY_ENABLED` now also applies to `local`.
- **BREAKING:** Remove the ElevenLabs provider: `tts/elevenlabs.py`, the `ELEVENLABS_*` settings, the stack env entries and the DEPLOY.md section. `NARRATION_PROVIDER` accepts only `local` (default) and `custom`.
- **BREAKING:** An unknown `NARRATION_PROVIDER` value, including the removed `elevenlabs`, now fails fast at startup. Today it is silently treated as neither local nor cloud, and jobs would sit in the queue forever.
- XTTS-v2 and F5-TTS stay selectable on the worker (`TTS_ENGINE=xtts|f5`) as a fallback. Removing them, and slimming the worker image, is deferred to a follow-up change.

## Capabilities

### New Capabilities
- `narration-synthesis`: How the home sound-worker turns a claimed narration job into audio. It covers the engine selection, the VoiceStudio request contract, per-language voice profiles, long-script chunking and audio assembly, waiting on readiness, and failure reporting.
- `narration-provider`: Which narration backends the VPS supports (`local`, `custom`) and how they are selected and validated. It covers removing ElevenLabs, failing fast on unknown values, and the claim contract, which now includes `language`.

### Modified Capabilities
- `tts-provider`: drop ElevenLabs from the configurable backends (`local` or `custom` only; `elevenlabs` now fails at startup), and limit "cloud providers run on the server" to the custom HTTP provider.
- `podcast-production`: the pluggable narration backend is now the local worker (VoiceStudio by default) or a custom HTTP model; ElevenLabs is removed.

## Impact

- **Sound-worker** (`sound-worker/src/sound_worker/`): a new VoiceStudio client, new settings in `config.py`, engine dispatch in `worker.py`, and tests (the package has none yet). The README is updated.
- **Pipeline** (`pipeline/src/boosternews/`): delete `tts/elevenlabs.py`. Prune `tts/__init__.py` (`get_provider`, `voice_for`, docstring) and `config.py` (`elevenlabs_*` fields, provider validation). `repository.claim_next_job` and the `/narration/claim` payload gain `language`. Comments in `scheduler.py` and `narration/service.py` are updated.
- **Deploy**: `deploy/compose.home.yml` and `deploy/docker-compose.yml` (worker profile) gain a `voicestudio` service. `deploy/stack.boosternews.yml` drops `ELEVENLABS_*`. `deploy/DEPLOY.md`, `deploy/voice/README.md` and `.env.example` are updated.
- **Operations**: a one-time step on the home machine creates the cloned-voice profile(s) in the VoiceStudio UI from `deploy/voice/reference*.wav`. The first run downloads about 2.4 GB of model weights. Production `.env` files must change `NARRATION_PROVIDER=elevenlabs` to `local` before upgrading.
- **Dependencies/licensing**: a new runtime dependency on the `ghcr.io/debpalash/voicestudio` image (AGPL-3.0, run unmodified as a separate service over HTTP). The licenses of the model weights (OmniVoice) must be checked in VoiceStudio's Model Manager. The `ElevenLabs` API key and subscription are no longer needed.
