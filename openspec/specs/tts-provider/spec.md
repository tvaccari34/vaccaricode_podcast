# Tts Provider

## Purpose
A pluggable text-to-speech provider abstraction for narrating podcast scripts in the owner's cloned voice.

## Requirements

### Requirement: Configurable narration backend
The system SHALL let an operator choose the text-to-speech backend by configuration — local GPU
worker, ElevenLabs, or a custom HTTP model — without code changes.

#### Scenario: Default is the local worker
- **WHEN** no narration provider is configured
- **THEN** narration uses the local GPU sound-worker exactly as before

#### Scenario: Switch to ElevenLabs
- **WHEN** the operator sets the provider to ElevenLabs with an API key and voice
- **THEN** subsequent narration is synthesized via ElevenLabs, with no other change to the pipeline

### Requirement: Common synthesis interface
Every provider SHALL expose the same operation: given text, a voice, and a language, return audio.
Downstream assembly (intro/outro, normalization, encoding) and storage SHALL be identical regardless
of provider.

#### Scenario: Same episode lifecycle across providers
- **WHEN** an episode is narrated by any provider
- **THEN** the resulting audio is assembled, stored, and attached to the episode through the same
  path, and the episode becomes ready/published the same way

### Requirement: Cloud providers run on the server
When a cloud provider is selected, narration SHALL be produced on the server without requiring the
home GPU machine.

#### Scenario: No home worker needed
- **WHEN** the provider is ElevenLabs or a custom HTTP model and a narration job is queued
- **THEN** the server synthesizes and completes the job, even if the home worker is offline

#### Scenario: Only one backend drains the queue
- **WHEN** a cloud provider is active and the home worker is still running
- **THEN** the home worker is served no jobs, so a job is never synthesized twice

### Requirement: Bring-your-own model via HTTP
The custom provider SHALL call a configurable HTTP endpoint (generic JSON or an OpenAI-compatible
speech API) so the operator can use a self-hosted or third-party voice model.

#### Scenario: Custom endpoint returns audio
- **WHEN** the custom provider posts narration text to the configured endpoint
- **THEN** the returned audio is used as the episode narration

### Requirement: Failures retry, never crash the pipeline
A provider error SHALL fail only that narration job (with retry up to its attempt limit); queued jobs
SHALL persist while a backend is unavailable.

#### Scenario: Provider temporarily down
- **WHEN** the active provider returns errors
- **THEN** the job retries and, if it exhausts attempts, is marked failed, while other jobs remain
  queued for when the provider recovers
