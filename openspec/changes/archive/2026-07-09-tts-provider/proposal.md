## Why

Podcast narration currently runs **only** on the home GPU sound-worker (F5-TTS / XTTS-v2 zero-shot
cloning). The clone quality isn't accurate enough, and the owner wants to switch to a higher-quality
option — **ElevenLabs** (managed voice cloning) or a **self-hosted / custom voice model** — without
rewriting the pipeline.

Right now the TTS engine is hard-wired into the home worker, and cloud synthesis has no place to run
(the whole narration path assumes the home GPU). We want a **pluggable TTS provider** so narration
can use the local GPU (today), ElevenLabs, or a custom HTTP endpoint, selected by configuration —
and switching providers should be a config change, not a rewrite.

## What Changes

- A **TTS provider interface** — `synthesize(text, voice, language) -> audio bytes` — with
  implementations:
  - **ElevenLabs** (cloud voice cloning via its API),
  - **Custom HTTP** (your own/self-hosted model or any OpenAI-compatible `/v1/audio/speech`),
  - **Local GPU worker** (the existing F5/XTTS home worker — kept, unchanged).
- A **`NARRATION_PROVIDER`** setting selects the active backend (default `local` → no behavior change).
- For **cloud providers, narration runs on the VPS** (no home PC required): a VPS-side drainer claims
  queued narration jobs and synthesizes via the provider, then reuses the **existing** assemble →
  store → mark-episode-ready → rebuild path. For `local`, the home worker drains as it does today.
- The narration **queue and all trigger points are unchanged** — `enqueue_narration` still enqueues a
  job; only *who drains it and how it's synthesized* depends on the provider.
- Because cloud TTS needs no GPU, it can optionally **auto-narrate the secondary language (English)**
  too, removing the manual-upload requirement (opt-in).

## Capabilities

### New Capabilities
- `tts-provider`: a pluggable narration backend — local GPU, ElevenLabs, or a custom HTTP model —
  chosen by configuration, with a common synthesize interface.

### Modified Capabilities
- `podcast-production`: narration is backend-agnostic; cloud providers synthesize on the VPS via the
  shared narration queue/completion path, and can narrate any language.

## Impact

- **New `boosternews.tts` package**: the provider protocol + `ElevenLabsProvider` + `CustomHttpProvider`.
- **New VPS narration drainer** (a scheduler job) active only when `NARRATION_PROVIDER != local`;
  the home worker stays the drainer for `local`. The `/narration/claim` endpoint returns no jobs to
  the home worker when the provider is cloud (prevents double-draining).
- **Refactor** the narration `/complete` logic into a shared `complete_narration()` reused by both
  the home-worker upload and the VPS drainer.
- **Config**: `NARRATION_PROVIDER`, `ELEVENLABS_API_KEY` / `ELEVENLABS_MODEL` / voice ids per
  language, `CUSTOM_TTS_URL` / key / format, and an opt-in to auto-narrate the secondary language.
- **Reused unchanged**: `narration_jobs` queue, `audio.assemble` (ffmpeg), object storage, episode
  lifecycle, the home worker (`sound-worker/`), and the review/publish flow.
- **Operational**: ElevenLabs bills per character (note cost); a custom self-hosted model is free but
  you run it. Switching is `NARRATION_PROVIDER=elevenlabs` (+ key/voice) and a redeploy.
