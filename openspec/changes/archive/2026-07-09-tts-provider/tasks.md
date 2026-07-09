# Tasks — pluggable TTS provider

## 1. Provider package
- [x] 1.1 `boosternews/tts/__init__.py`: `TTSProvider` protocol (`synthesize(text, *, voice, language) -> bytes`) + `get_provider()` factory keyed on `NARRATION_PROVIDER`.
- [x] 1.2 `ElevenLabsProvider`: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice}` with `xi-api-key`, `model_id`, returns mp3 bytes; voice/model/key from config.
- [x] 1.3 `CustomHttpProvider`: POST to `CUSTOM_TTS_URL` — `generic` body `{text,voice,language,format}` or `openai` body `{model,input,voice,response_format}`; returns audio bytes.

## 2. Config
- [x] 2.1 Add `narration_provider` (local|elevenlabs|custom) + ElevenLabs/custom credentials, models, per-language voice ids, `narration_secondary_enabled` (defaults keep current behavior).

## 3. Shared completion + VPS drainer
- [x] 3.1 Refactor narration `/complete` into `narration.complete_narration(episode_id, job_id, raw_audio)` (store raw → assemble → upload → `update_episode_audio` → `complete_job` → `request_site_rebuild`); `/complete` route calls it.
- [x] 3.2 `narration.drain_once(limit)`: claim queued jobs, `provider.synthesize(...)`, `complete_narration(...)`, `fail_job` on error. Skips work when `NARRATION_PROVIDER == local`.
- [x] 3.3 Scheduler `narrate` job (enabled when provider != local) calling `drain_once`.

## 4. Prevent double-drain
- [x] 4.1 `POST /narration/claim` returns 204 when `NARRATION_PROVIDER != local` (home worker gets no jobs while a cloud provider is active).

## 5. Secondary-language narration (optional)
- [x] 5.1 When `narration_secondary_enabled` and provider is cloud, enqueue narration for the secondary-language episode too (generate + re-narrate paths).

## 6. Verify end-to-end
- [x] 6.1 `local` (default): unchanged — home worker still narrates; VPS drainer idle; `/claim` serves jobs.
- [x] 6.2 `elevenlabs`: set key + voice; re-narrate an episode → VPS drainer synthesizes → episode `ready` with audio; compare quality vs local.
- [x] 6.3 `custom` (generic + openai modes): a stub/self-hosted endpoint returns audio → episode narrated.
- [x] 6.4 Provider error → job retries then `failed`; `/claim` returns 204 for the home worker under a cloud provider.
- [x] 6.5 (If enabled) secondary-language episode is auto-narrated.

## 7. Docs
- [x] 7.1 `deploy/DEPLOY.md` / `sound-worker/README.md`: provider options, config, ElevenLabs setup (create a voice → voice id), custom-endpoint contract, cost note, and how to switch/revert.
