# Design — pluggable TTS provider

## Context

Narration flows through a queue: any trigger (`generate`, dashboard re-narrate, `enqueue-narration`)
calls `repo.enqueue_narration(episode_id, voice_id, text)` → a `narration_jobs` row. Today the **home
GPU worker** (`sound-worker/`) claims jobs via `POST /api/narration/claim`, synthesizes with F5/XTTS,
and `POST /api/narration/{id}/complete` (audio). The VPS `/complete` handler then does everything
downstream: store raw wav, `audio.assemble` (ffmpeg normalize/intro/outro → mp3), upload, mark the
episode ready/published, complete the job, and queue a site rebuild.

The engine is hard-wired in the worker; there is nowhere for a cloud API to run.

## Goals

- Swap the narration backend by config: `local` (GPU worker), `elevenlabs`, or `custom` (HTTP).
- Reuse the queue, ffmpeg assembly, storage, and episode lifecycle untouched.
- No behavior change when `NARRATION_PROVIDER=local` (the default).

## Non-Goals

- Replacing the home worker (it stays as the `local` backend).
- Real-time/streaming TTS; per-word timing; multi-voice dialogue.
- A universal adapter for every TTS vendor — ElevenLabs + a generic HTTP contract cover the ask.

## Key decisions

### 1. The provider interface is just synthesis
```python
class TTSProvider(Protocol):
    def synthesize(self, text: str, *, voice: str, language: str) -> bytes: ...  # raw audio (wav/mp3)
```
Assembly (intro/outro, loudness normalize, mp3 encode) stays on the VPS via the existing
`audio.assemble` — providers only return raw speech. This keeps output consistent across backends.

### 2. Two execution models, one queue
`enqueue_narration` and every trigger stay **unchanged**. What differs is the drainer:
- **`local`** → the home GPU worker claims + synthesizes + uploads (today's path). The VPS drainer is
  inactive.
- **`elevenlabs` / `custom`** → a **VPS-side drainer** claims queued jobs, calls
  `provider.synthesize(...)`, and runs the shared completion. The home worker is not used.

Only one drainer may run. To prevent a double-drain if the home worker is left running while a cloud
provider is active, `POST /narration/claim` returns `204` (no work) to external workers whenever
`NARRATION_PROVIDER != local`.

### 3. Refactor `/complete` into a shared function
Extract the store→assemble→store→`update_episode_audio`→`complete_job`→`request_site_rebuild` logic
into `narration.complete_narration(episode_id, job_id, raw_audio: bytes)`. Both the home-worker
`/complete` route and the VPS drainer call it, so the mp3 output and episode lifecycle are identical
regardless of provider.

### 4. Where the VPS drainer runs
A **scheduler job** (`narrate`), enabled only when `NARRATION_PROVIDER != local`, that on each tick
claims up to N queued jobs and processes them. Rationale: reuses the already-running scheduler and its
retry/isolation; a ~30s tick is fine for podcast latency. (Alternative: a dedicated always-on drainer
service for lower latency — deferred.)

### 5. Voice mapping is per-provider, resolved from config
`voice_id` means different things per backend, so the provider resolves the real voice from config by
language rather than trusting the job's `voice_id`:
- `local`: the cloned-voice reference id (`tiago`) — unchanged.
- `elevenlabs`: `ELEVENLABS_VOICE_ID` (and `_EN`) — the voice id from your ElevenLabs instant/pro
  clone.
- `custom`: `CUSTOM_TTS_VOICE` (and `_EN`), passed through to your endpoint.

### 6. Custom HTTP contract (bring your own model)
`CustomHttpProvider` POSTs to `CUSTOM_TTS_URL` with `Authorization: Bearer $CUSTOM_TTS_API_KEY` and a
JSON body `{ "text": ..., "voice": ..., "language": ..., "format": "mp3" }`, expecting audio bytes in
the response (content-type audio/*). An **OpenAI-compatible mode** (`CUSTOM_TTS_FORMAT=openai`) instead
sends `{ "model", "input", "voice", "response_format" }` to a `/v1/audio/speech`-style endpoint. This
covers self-hosted servers and OpenAI-compatible TTS with one small provider.

### 7. Secondary-language narration (optional)
Cloud providers need no GPU, so English can be auto-narrated too. Gate behind
`NARRATION_SECONDARY_ENABLED` (default off → today's manual-upload behavior). When on and the provider
is cloud, `generate`/re-narrate also enqueue the secondary-language episode.

### 8. Failure handling is unchanged
Provider errors → `fail_job` (retries up to `max_attempts`, then `failed`), exactly as today. If the
active backend is down, jobs stay queued.

## Config (all optional; defaults preserve current behavior)
```
NARRATION_PROVIDER=local            # local | elevenlabs | custom
ELEVENLABS_API_KEY=
ELEVENLABS_MODEL=eleven_multilingual_v2
ELEVENLABS_VOICE_ID=                 # + ELEVENLABS_VOICE_ID_EN
CUSTOM_TTS_URL=
CUSTOM_TTS_API_KEY=
CUSTOM_TTS_VOICE=                    # + CUSTOM_TTS_VOICE_EN
CUSTOM_TTS_FORMAT=generic           # generic | openai
NARRATION_SECONDARY_ENABLED=false
```

## Rollout / reversibility
Default `local` = zero change. To try ElevenLabs: set the key + voice id + `NARRATION_PROVIDER=
elevenlabs`, redeploy scheduler/narration-api. To A/B: re-narrate one episode under each provider and
compare. Revert = set `NARRATION_PROVIDER=local`. The home worker and its F5/XTTS code remain intact.

## Risks / trade-offs
- **Cost**: ElevenLabs bills per character; a long episode is many characters. Note it; the weekly
  cadence keeps volume low.
- **Double-drain**: mitigated by the `/claim` guard (§2).
- **Voice parity across languages**: separate voice ids per language; if `_EN` is unset, fall back to
  the primary voice.

## Alternatives considered
- **Add an `elevenlabs` engine inside the home worker** — rejected: still requires the home PC to be
  on, defeating the point of a cloud API.
- **Synthesize inline at generate time** (no queue) — rejected: couples LLM generation to TTS, loses
  retry/queue semantics and the re-narrate flow.
