## MODIFIED Requirements

### Requirement: Configurable narration backend
The system SHALL let an operator choose the text-to-speech backend by configuration — the local GPU
worker (which synthesizes through a self-hosted VoiceStudio by default) or a custom HTTP model —
without code changes. ElevenLabs is no longer a supported backend.

#### Scenario: Default is the local worker
- **WHEN** no narration provider is configured
- **THEN** narration uses the local GPU sound-worker exactly as before

#### Scenario: ElevenLabs is rejected
- **WHEN** the operator sets the provider to `elevenlabs`
- **THEN** startup fails with a message to use `local` (home VoiceStudio worker) or `custom`

### Requirement: Cloud providers run on the server
When the custom HTTP provider is selected, narration SHALL be produced on the server without
requiring the home GPU machine.

#### Scenario: No home worker needed
- **WHEN** the provider is a custom HTTP model and a narration job is queued
- **THEN** the server synthesizes and completes the job, even if the home worker is offline

#### Scenario: Only one backend drains the queue
- **WHEN** a cloud provider is active and the home worker is still running
- **THEN** the home worker is served no jobs, so a job is never synthesized twice
