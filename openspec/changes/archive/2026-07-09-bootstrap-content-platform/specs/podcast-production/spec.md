## ADDED Requirements

### Requirement: Self-hosted GPU sound-worker
The system SHALL provide a self-hosted GPU sound-worker that converts a podcast script into
speech audio using an open neural TTS model, processing narration as queued jobs.

#### Scenario: Synthesize narration from a script
- **WHEN** a narration job for a podcast script is available to the worker
- **THEN** the worker produces speech audio rendered with the configured voice and makes it
  available to the pipeline

#### Scenario: Sound-worker unavailable
- **WHEN** no sound-worker is available to process narration jobs
- **THEN** narration jobs remain queued and the episode stays in a non-published state for
  later processing, without blocking other pipeline work

#### Scenario: Synthesis fails for a job
- **WHEN** a sound-worker fails while synthesizing a narration job
- **THEN** the failure is recorded and the job is eligible to be retried, leaving the episode
  unpublished until narration succeeds

### Requirement: Cloned-voice narration
The system SHALL narrate episodes by default in the owner's cloned voice, built from a
registered reference speech sample, and SHALL use that voice consistently across an episode.

#### Scenario: Register the owner's voice
- **WHEN** the owner provides a reference speech sample to the sound-worker
- **THEN** a cloned voice is created from that sample and becomes the default narration voice

#### Scenario: Episode narrated in the cloned voice
- **WHEN** synthesis runs for an episode without an explicit voice override
- **THEN** the owner's cloned voice is used consistently from start to finish of the episode

#### Scenario: No cloned voice registered
- **WHEN** synthesis is requested but no cloned voice has been registered yet
- **THEN** the system reports that a reference sample is required rather than silently using a
  different voice

### Requirement: Episode audio assembly
The system SHALL assemble the synthesized narration into a publishable episode by adding
intro/outro, normalizing loudness, encoding to a distributable format, and storing the file
in object storage.

#### Scenario: Produce a publishable episode file
- **WHEN** narration synthesis completes for an episode
- **THEN** the system produces a loudness-normalized, encoded audio file (with intro/outro)
  stored in object storage, with its duration and URL recorded on the episode

#### Scenario: Episode metadata for the feed
- **WHEN** an episode file is produced
- **THEN** title, description/show notes, duration, file size, and audio URL are recorded so
  the podcast feed can reference the episode
