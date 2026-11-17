## 1. Pipeline: remove ElevenLabs and validate the provider

- [x] 1.1 Delete `pipeline/src/boosternews/tts/elevenlabs.py`
- [x] 1.2 In `tts/__init__.py`, drop the `elevenlabs` branches from `get_provider` and `voice_for`, and update the module docstring (`local` | `custom`)
- [x] 1.3 In `config.py`, remove the `elevenlabs_*` fields, update the narration comments (secondary narration now applies to `local` too), and add a `narration_provider` validator that normalizes case and rejects anything other than `local`/`custom`, with an explicit message for `elevenlabs`
- [x] 1.4 Update the ElevenLabs mentions in comments and docstrings in `scheduler.py` and `narration/service.py`
- [x] 1.5 Add `test_config.py` cases: default `local`; `CUSTOM` normalizes to `custom`; `elevenlabs` and `foo` raise; stray `ELEVENLABS_API_KEY` is ignored

## 2. Pipeline: add language to the claim response

- [x] 2.1 Change `repository.claim_next_job` to join `episodes` and return `language`, falling back to `PRIMARY_LANGUAGE_CODE` when it is null
- [x] 2.2 Check that `/narration/claim` returns the new field (no route change expected) and that `drain_once` still works with the extra key
- [x] 2.3 Add a test that a claimed secondary-language job carries `"language": "en"` and a null-language episode carries the primary code

## 3. Sound-worker: VoiceStudio engine

- [x] 3.1 Add settings to `config.py`: `voicestudio_url` (default `http://voicestudio:3900`), `voicestudio_api_key`, `voicestudio_model` (`omnivoice`), `voicestudio_voice`, `voicestudio_voice_en`, `voicestudio_max_chars` (2000), `voicestudio_timeout_seconds` (600), `secondary_language_code` (`en`). Change the `tts_engine` default to `voicestudio` and validate it against `voicestudio|xtts|f5`
- [x] 3.2 Add `sound_worker/voicestudio.py`: `chunk_text` (ported from the pipeline), `voice_for(language)`, `iso639_1(code)`, `health_ok(client)`, and `synthesize(text, language) -> bytes`, which POSTs each chunk to `/v1/audio/speech` with `response_format="pcm"`, concatenates the PCM and wraps it in a 24 kHz mono 16-bit WAV with `wave`. Raise with VoiceStudio's `error.message` on non-200
- [x] 3.3 In `worker.py`, make `synthesize` take the job's `language`. Dispatch `voicestudio` to the new module, which needs no reference-file check, and keep the `xtts`/`f5` paths unchanged, including their reference-sample check
- [x] 3.4 In `worker.run`, with the `voicestudio` engine, skip claiming while `/health` is not 200 (log it and sleep `poll_interval_seconds`), and pass `job.get("language")` through to `synthesize`
- [x] 3.5 Create `sound-worker/tests/` with an httpx `MockTransport`. Cover: request body and Bearer header; per-language voice selection and the `pt-BR`→`pt` mapping; a missing profile fails without a request; a 9k-char script yields several ≤2000-char requests and one valid WAV of the summed length; a non-200 status surfaces the error message; an unknown `TTS_ENGINE` raises; `normalize_for_tts` behaviour stays the same

## 4. Deploy

- [x] 4.1 Pick and pin the current stable VoiceStudio release tag (check GitHub releases)
- [x] 4.2 Add a `voicestudio` service to `deploy/compose.home.yml`: the pinned image, NVIDIA GPU reservation, `OMNIVOICE_API_KEY`, `OMNIVOICE_DATA_DIR=/app/omnivoice_data`, `OMNIVOICE_ANALYTICS_DISABLED=1`, the named volume `voicestudio-data` and `127.0.0.1:3900:3900`, relying on the image's built-in `/health` HEALTHCHECK (see design D6). Make `sound-worker` `depends_on: voicestudio: condition: service_healthy` and pass the `VOICESTUDIO_*`/`TTS_ENGINE` env
- [x] 4.3 Mirror the service under the `worker` profile in `deploy/docker-compose.yml` (all-in-one local) and check that `make worker` still works
- [x] 4.4 Remove the `ELEVENLABS_*` lines from `deploy/stack.boosternews.yml`
- [x] 4.5 Add a "Narration (VoiceStudio, home GPU)" block to `.env.example` with `TTS_ENGINE`, `VOICESTUDIO_*` and `OMNIVOICE_API_KEY`, and a note that `NARRATION_PROVIDER=elevenlabs` is no longer valid

## 5. Docs

- [x] 5.1 In `deploy/DEPLOY.md`, replace the ElevenLabs provider section with the VoiceStudio home setup, add migration steps from ElevenLabs, and update the architecture diagram text (XTTS-v2 → VoiceStudio)
- [x] 5.2 In `sound-worker/README.md`, document the engines, the VoiceStudio config table, the health gating and the provenance watermark note
- [x] 5.3 In `deploy/voice/README.md`, describe creating the VoiceStudio voice profile(s) from the reference WAVs, including the consent step and copying the profile ids into `.env`
- [x] 5.4 Note the VoiceStudio (AGPL-3.0, separate service) and model-weight licensing in `README.md` or `DEPLOY.md`

## 6. Verification and cutover

- [x] 6.1 Run `pytest` in `pipeline/` and `sound-worker/` and `ruff check` on both
- [x] 6.2 On the home GPU box, start the stack, wait for `/health`, create the profiles, and `curl` `/v1/audio/speech` for one pt-BR and one EN paragraph
- [x] 6.3 End to end: re-narrate one pt-BR and one EN episode from the dashboard, then confirm the mp3 in MinIO, the episode page and the podcast feed. Done locally 2026-11-13 (this checkout's narration API + worker against the local stack, the pt-BR VoiceStudio profile, 32 steps): 2 pt-BR + 2 EN episodes narrated, published pair stayed published, a scratch Astro build showed the new MP3s on both episode pages and both feeds. Production run happens with 6.5
- [x] 6.4 A/B listen against the F5 output and the last ElevenLabs episode, then resolve the open questions in design.md (`num_step`, `seed`, single or dual profile). Done 2026-11-13: `num_step` 32 (now `VOICESTUDIO_NUM_STEP`), no fixed `seed`, single profile. Compared against F5 only; the ElevenLabs A/B was skipped
- [x] 6.5 Production cutover per the design.md migration plan (set `NARRATION_PROVIDER=local` before deploying the VPS change), then `openspec archive switch-narration-to-voicestudio`. Runbook: `deploy/VOICESTUDIO_CUTOVER.md` (server script `deploy/voicestudio-cutover.sh`). Done 2026-11-13/16: VPS on 04d9759 with `NARRATION_PROVIDER=local` and `NARRATION_SECONDARY_ENABLED=true`; home worker `home-4060ti` on `TTS_ENGINE=voicestudio` from the `boosternews-voicestudio` worktree; pt-BR and EN episodes narrated in production. Pre-cutover English audio (ElevenLabs, `claimed_by=vps-narrator`) is not re-queued on approval and was re-narrated by hand
- [x] 6.6 Dashboard: when `NARRATION_SECONDARY_ENABLED=true`, English episodes get edit-script & re-narrate (manual upload kept) and Create Episode can queue English narration; tests in `pipeline/tests/test_dashboard_secondary_narration.py`
