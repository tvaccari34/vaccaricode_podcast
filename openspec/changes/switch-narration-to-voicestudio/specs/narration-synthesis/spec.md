## ADDED Requirements

### Requirement: Selectable synthesis engine
The sound-worker SHALL select its synthesis engine from `TTS_ENGINE`. The accepted values are `voicestudio` (default), `xtts` and `f5`. Any other value MUST make the worker exit at startup with an error that names the setting.

#### Scenario: Default engine
- **WHEN** the worker starts without `TTS_ENGINE` set
- **THEN** it synthesizes claimed jobs through VoiceStudio

#### Scenario: Legacy engine still selectable
- **WHEN** the worker starts with `TTS_ENGINE=f5`
- **THEN** it synthesizes claimed jobs with F5-TTS from the local reference sample, as before this change

#### Scenario: Unknown engine
- **WHEN** the worker starts with `TTS_ENGINE=elevenlabs`
- **THEN** it exits before claiming any job and logs that `TTS_ENGINE` must be one of `voicestudio`, `xtts`, `f5`

### Requirement: VoiceStudio speech request
When the engine is `voicestudio`, the worker SHALL synthesize by sending `POST {VOICESTUDIO_URL}/v1/audio/speech` with a JSON body containing `model` (`VOICESTUDIO_MODEL`, default `omnivoice`), `input` (the normalized text chunk), `voice` (the resolved voice profile), `language` (the ISO 639-1 base subtag of the job's language, e.g. `pt-BR` → `pt`), `response_format: "pcm"`, `speed` (`TTS_SPEED`) and `num_step` (`VOICESTUDIO_NUM_STEP`, default 32). When `VOICESTUDIO_API_KEY` is set, the request MUST carry `Authorization: Bearer <key>`.

#### Scenario: Authenticated request
- **WHEN** a job is synthesized with `VOICESTUDIO_API_KEY=abc`
- **THEN** every `/v1/audio/speech` request carries the header `Authorization: Bearer abc`

#### Scenario: Error from VoiceStudio
- **WHEN** VoiceStudio answers a speech request with a non-200 status
- **THEN** the worker reports the job as failed to the VPS with an error message that includes the status and VoiceStudio's `error.message`, and the worker keeps polling

### Requirement: Per-language voice profile
The worker SHALL map the job's `language` to a VoiceStudio voice profile. The secondary language (`SECONDARY_LANGUAGE_CODE`) uses `VOICESTUDIO_VOICE_EN` when that is set. Every other language, and the secondary language when `VOICESTUDIO_VOICE_EN` is empty, uses `VOICESTUDIO_VOICE`. If the resolved profile is empty, the job MUST fail with a message naming the missing setting. The worker MUST NOT fall back to an engine default voice.

#### Scenario: Secondary-language job
- **WHEN** a job with `language=en` is claimed, `SECONDARY_LANGUAGE_CODE=en` and `VOICESTUDIO_VOICE_EN=owner-en`
- **THEN** the request uses `voice=owner-en` and `language=en`

#### Scenario: Primary-language job
- **WHEN** a job with `language=pt-BR` is claimed and `VOICESTUDIO_VOICE=owner-pt`
- **THEN** the request uses `voice=owner-pt` and `language=pt`

#### Scenario: Job without a language
- **WHEN** a claimed job has no `language` field (a VPS from before this change)
- **THEN** the worker uses `LANGUAGE` as the language and `VOICESTUDIO_VOICE` as the profile

#### Scenario: No profile configured
- **WHEN** `VOICESTUDIO_VOICE` is empty and a primary-language job is claimed
- **THEN** the job is reported failed with an error that names `VOICESTUDIO_VOICE`, and no speech request is sent

### Requirement: Long scripts are chunked and assembled into one WAV
The worker SHALL normalize the script with the existing `normalize_for_tts`. It SHALL split the result into chunks no longer than `VOICESTUDIO_MAX_CHARS` (default 2000, which MUST stay below VoiceStudio's 4096-character input limit), preferring paragraph and then sentence boundaries. It SHALL synthesize the chunks in order, concatenate the returned raw PCM (24 kHz, 16-bit little-endian, mono) and upload a single valid WAV file.

#### Scenario: Script longer than one chunk
- **WHEN** a job's text is 9,000 characters
- **THEN** the worker sends several speech requests, each with `input` of at most 2000 characters and none splitting a sentence that fits within the limit, and uploads one WAV whose duration is the sum of the chunks

#### Scenario: Uploaded audio is a valid WAV
- **WHEN** synthesis of a job completes
- **THEN** the uploaded `narration.wav` has a RIFF/WAVE header declaring 24000 Hz, 1 channel and 16 bits, and the VPS assembles it into the episode mp3 without errors

### Requirement: Readiness before claiming
With the `voicestudio` engine, the worker SHALL NOT claim a job while `GET {VOICESTUDIO_URL}/health` does not return 200. While it waits, it SHALL log the state and retry on the normal poll interval, so that a job's attempts are not spent while models load.

#### Scenario: VoiceStudio still starting
- **WHEN** `/health` returns 503 because the models are still downloading
- **THEN** the worker does not call `/narration/claim` and checks `/health` again after `POLL_INTERVAL_SECONDS`

#### Scenario: VoiceStudio becomes healthy
- **WHEN** `/health` returns 200
- **THEN** the worker resumes claiming jobs

### Requirement: Synthesis timeout
Each VoiceStudio speech request SHALL use the timeout `VOICESTUDIO_TIMEOUT_SECONDS` (default 600). This timeout is separate from the VPS request timeout. A timed-out request MUST fail the job rather than hang the worker loop.

#### Scenario: Chunk times out
- **WHEN** a speech request takes longer than `VOICESTUDIO_TIMEOUT_SECONDS`
- **THEN** the job is reported failed with a timeout error, and the worker claims the next job
