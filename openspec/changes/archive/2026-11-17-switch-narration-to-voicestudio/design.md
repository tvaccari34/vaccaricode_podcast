## Context

Narration today has two paths, chosen by `NARRATION_PROVIDER`:

- **`local`**: the home GPU sound-worker (`sound-worker/`) pulls jobs from the VPS over outbound HTTPS (`/narration/claim` → synthesize → `/narration/{id}/complete`). It synthesizes in-process with XTTS-v2 or F5-TTS (`TTS_ENGINE`), from `deploy/voice/reference_pt.wav`. The home network has no inbound ports.
- **`elevenlabs` / `custom`**: the VPS scheduler drains the queue itself (`narration/service.py:drain_once`) through `tts.get_provider()`. While one of these is active, `/narration/claim` returns 204 so a job is never synthesized twice.

ElevenLabs is the backend in use. The goal is to replace it with VoiceStudio (github.com/debpalash/voicestudio), running on the home GPU box.

What we confirmed about VoiceStudio by reading its source (`backend/api/routers/openai_compat.py`, `docs/api-auth.md`, `docs/install/docker.md`):

- It has an OpenAI-compatible `POST /v1/audio/speech` endpoint. The body takes `model` (default `omnivoice`), `input` (≤ 4096 chars), `voice` (a voice-profile id or name; OpenAI names such as `alloy` map to the engine default), `response_format` (`mp3|opus|aac|flac|wav|pcm`, where `pcm` is raw 24 kHz s16le mono), `speed`, and the extensions `language`, `seed`, `num_step` and `guidance_scale`. Errors come back in OpenAI's `{"error": {...}}` shape.
- Auth is `Authorization: Bearer $OMNIVOICE_API_KEY` for scripts. Loopback clients need no credential.
- The Docker image is `ghcr.io/debpalash/voicestudio` with tags `:stable`, `:X.Y.Z` and others. It listens on port 3900, keeps data, voices and the HF model cache in `/app/omnivoice_data`, and reports `GET /health` as 503 during startup and 200 once ready. The first run downloads about 2.4 GB of weights. It needs the NVIDIA Container Toolkit for GPU.
- Voice cloning works through voice profiles (`/profiles` in the app API, with consent and attestation endpoints), created in the web UI from a reference recording.

## Goals / Non-Goals

**Goals:**
- Narrate both languages in the owner's cloned voice through VoiceStudio on the home GPU, with no per-character cost and no voice data off-premises.
- Keep the outbound-only home architecture and the existing VPS completion path (`complete_narration`) unchanged.
- Remove ElevenLabs completely, and make a stale `NARRATION_PROVIDER=elevenlabs` fail loudly instead of silently stalling the queue.

**Non-Goals:**
- Removing XTTS/F5 from the worker or slimming its CUDA image. That is a follow-up once VoiceStudio has proven itself in production.
- Running VoiceStudio on the VPS, or exposing the home box to inbound traffic.
- Automating voice-profile creation. It is a one-time manual step that includes a consent attestation.
- Changing the `custom` HTTP provider. It already speaks the OpenAI format and could point at a VoiceStudio instance elsewhere if that is ever needed.

## Decisions

### D1. VoiceStudio is a worker *engine*, not a VPS *provider*
The sound-worker gets `TTS_ENGINE=voicestudio` and calls VoiceStudio at `http://voicestudio:3900` on the home compose network.
- *Alternative:* add a `voicestudio` VPS provider and have the drainer call home over a tunnel. Rejected because it needs inbound reachability (Tailscale or Cloudflare Tunnel), which breaks the "no inbound ports at home" property. The pull model also already handles a home PC that is asleep: jobs simply wait.
- *Alternative:* run VoiceStudio on the VPS CPU. Rejected because it is too slow for full podcast scripts and adds a large image to the VPS.

### D2. Use `/v1/audio/speech` with `response_format: "pcm"` and assemble the WAV in the worker
Scripts exceed the 4096-char input cap, so we chunk them. Raw PCM chunks concatenate trivially, unlike WAV or MP3 containers. The worker then writes a single RIFF header with the stdlib `wave` module (24000 Hz, mono, 16-bit) and uploads `narration.wav`, the same contract XTTS and F5 use today. The VPS's ffmpeg `assemble` is untouched.
- *Alternative:* `wav` per chunk with an ffmpeg concat. This needs ffmpeg in the worker's code path and temp files, and gains nothing.
- *Alternative:* VoiceStudio's `longform_jobs` router, which chunks server-side. It is undocumented, asynchronous and needs polling, so it is more surface to depend on. We can revisit it if per-chunk prosody seams are audible.
- The chunker is a small local copy of the pipeline's `tts.chunk_text`, because the worker is a separate package with no dependency on `boosternews`. The default limit of 2000 chars leaves headroom under 4096 and keeps each request short enough for the timeout.

### D3. Language travels with the job
`repository.claim_next_job` joins `episodes` to return `language` (falling back to `PRIMARY_LANGUAGE_CODE`). The worker reduces it to the ISO 639-1 base (`pt-BR` → `pt`) for VoiceStudio and picks `VOICESTUDIO_VOICE` or `VOICESTUDIO_VOICE_EN`, mirroring the existing `tts.voice_for` rules. This is additive, so an old worker still works, and a new worker talking to an old VPS falls back to `LANGUAGE`. It is also what makes `NARRATION_SECONDARY_ENABLED` useful under `local`.

### D4. Gate claiming on `/health`
VoiceStudio can take minutes to become ready on first boot because of the weight download. The worker checks `/health` before each claim and skips the claim while it is not 200, so jobs don't spend their `max_attempts` on a cold start. Compose also sets `depends_on: condition: service_healthy`, but the worker-side check covers VoiceStudio restarts at runtime too.

### D5. Fail fast on provider config
`Settings.narration_provider` gets a validator that accepts `local` and `custom`. Today an unknown value makes `/narration/claim` return 204 *and* makes `drain_once` no-op, so jobs strand silently. Leftover `ELEVENLABS_*` env vars are harmless because settings use `extra="ignore"`.

### D6. Pin the image and harden the container
Use `ghcr.io/debpalash/voicestudio:<exact release>` (not `:stable`) so upgrades are deliberate. **Pinned to `0.5.7`** (released 2026-10-26). `v0.5.8` was released on the day of implementation and had no image published yet. Its `/v1/audio/speech` contract (`pcm`, `language`, 4096-char cap) and `/health` were checked against the v0.5.7 source. Set `OMNIVOICE_ANALYTICS_DISABLED=1` and `OMNIVOICE_API_KEY` from `.env`. Publish the UI only on `127.0.0.1:3900`, for the one-time profile setup. Keep `/app/omnivoice_data` on a named volume. *During implementation:* there is no `deploy/voice` mount, because the reference is uploaded through the browser from the host. There is also no compose `healthcheck`, because the image ships its own `HEALTHCHECK` on `/health`, which `depends_on: service_healthy` uses, and we can't assume `curl` exists in the image.

## Risks / Trade-offs

- **Voice quality and pt-BR accent may differ from F5 (pt-BR fine-tune) or ElevenLabs.** → Before cutover, A/B the same script across `voicestudio`, `f5` and the last ElevenLabs episode. XTTS and F5 stay one env var away (`TTS_ENGINE`). VoiceStudio's Model Manager can also switch the active engine (CosyVoice, IndexTTS2 and others) without code changes, through `VOICESTUDIO_MODEL`.
- **Audible seams between chunks.** → Chunk on paragraph and sentence boundaries. A two-chunk A/B render had no audible seam, so no fixed `seed` is sent. Fall back to D2's longform alternative if needed.
- **Young, fast-moving upstream (AGPL-3.0, many routers).** → Depend only on the OpenAI-compatible endpoint and `/health`, which have the most stable contract. Pin the image tag. Running it unmodified as a separate network service puts no copyleft obligation on BoosterNews. Model-weight licenses are separate and must be checked in the Model Manager before production use.
- **OmniVoice weights are CC-BY-NC (non-commercial).** The k2-fsa/OmniVoice model card says the code is Apache-2.0 but the pre-trained model is CC-BY-NC because of its training data (Emilia). The fallbacks share this limit: the F5-TTS base weights are CC-BY-NC for the same reason, and XTTS-v2 is under the Coqui Public Model License (non-commercial). → **Decision (2026-11-13):** keep `omnivoice` while the podcast is non-commercial; do not use its audio in ads or other business promotion. **Before any commercial use** (sponsorships, ads, paid products), switch to VoxCPM2: it is Apache-2.0, supports Portuguese, and installs as a VoiceStudio engine. Switching means installing it in the Model Manager and setting `VOICESTUDIO_MODEL=voxcpm2`, with no code change; A/B it first. CosyVoice 3 (Apache-2.0) and GPT-SoVITS (MIT) don't cover Portuguese.
- **Invisible provenance watermark** in VoiceStudio output (`services.watermark`). → This is acceptable, and arguably desirable for AI-narrated content. Note it in the README.
- **GPU contention** if XTTS or F5 is ever loaded alongside VoiceStudio. → With `TTS_ENGINE=voicestudio` the worker never imports torch models (lazy loading), so only VoiceStudio holds VRAM.
- **Losing a no-home-PC option.** With ElevenLabs gone, narration needs the home box to be on, and jobs queue until it is. → The user accepted this. `custom` remains available for any hosted OpenAI-compatible TTS.

## Migration Plan

1. On the home box: pull the pinned VoiceStudio image, start it, and wait for `/health` to return 200. Open `http://127.0.0.1:3900`, create the pt-BR (and optionally EN) voice profiles from `deploy/voice/reference*.wav`, complete the consent attestation, and copy the profile ids into the home `.env` (`VOICESTUDIO_VOICE`, `VOICESTUDIO_VOICE_EN`).
2. Smoke test by running `curl` against `/v1/audio/speech` with a paragraph in each language and listening to the result.
3. Deploy the pipeline change to the VPS and set `NARRATION_PROVIDER=local` in the same step, because `elevenlabs` now fails validation. Optionally set `NARRATION_SECONDARY_ENABLED=true`.
4. Deploy the worker with `TTS_ENGINE=voicestudio`. Re-narrate one episode from the dashboard and verify it plays end to end on the site and in the feed.
5. Remove `ELEVENLABS_*` from the production `.env` and cancel the ElevenLabs plan once a week of episodes has shipped.

**Rollback:** Set `TTS_ENGINE=f5` (or `xtts`) on the worker, with no VPS change. Rolling back to ElevenLabs means reverting this change's commit on the VPS and restoring the env vars.

## Open Questions

- ~~**Image tag:**~~ Resolved: `0.5.7` (see D6). Bump to `0.5.8` once its image is published and has had a couple of weeks to settle.
A/B listening on 2026-11-13 (home 16 GB consumer NVIDIA GPU, cloned profiles from ~60 s trimmed references) resolved the next three:

- ~~**Engine and quality preset:**~~ Resolved: `omnivoice` with **`num_step: 32`**. It sounded clearly better than 16 and took no measurable extra time (both ran at about 0.15× real time, so a 3-minute script renders in about 25 s). Exposed as `VOICESTUDIO_NUM_STEP` (default 32, range 1–128). VoiceStudio's UI pack tier does not affect `/v1/audio/speech`, so the worker sends this itself.
- ~~**Fixed `seed`** across chunks~~: Resolved: not needed. A 171 s, two-chunk pt-BR render had no audible seam or timbre shift at the join.
- ~~**One profile for both languages?**~~ Resolved: yes. English read by the pt-BR profile sounded as good as the dedicated English profile, so `VOICESTUDIO_VOICE_EN` stays optional and can be left unset.
- **Overall quality** sounded about the same as the current F5 pt-BR output. The A/B against an ElevenLabs episode was not done.
- **Follow-up:** once VoiceStudio is proven, drop XTTS and F5 and switch the worker to a slim Python image (no CUDA or torch), since VoiceStudio owns the GPU.
