## ADDED Requirements

### Requirement: Persistent pipeline state
The system SHALL persist pipeline state — topics, drafts, episodes, review decisions, and
publishing status — in a relational database (PostgreSQL).

#### Scenario: State survives restarts
- **WHEN** a pipeline service restarts
- **THEN** previously stored topics, drafts, and their statuses are still available and
  in-flight work can resume

### Requirement: Audio object storage
The system SHALL store produced audio files in S3-compatible object storage and reference
them by URL.

#### Scenario: Store and serve an episode file
- **WHEN** an episode audio file is produced
- **THEN** it is uploaded to object storage and a stable URL is recorded for the podcast feed
  and site to reference

### Requirement: Scheduled job orchestration
The system SHALL run ingestion and production work as scheduled/queued jobs that can be
triggered on a schedule and retried on failure.

#### Scenario: Failed job is retried
- **WHEN** a scheduled job fails
- **THEN** the failure is recorded and the job is eligible for retry without manual database
  edits

### Requirement: Containerized deployment with managed secrets
The system SHALL be deployable via Docker Compose with all services defined, and SHALL read
credentials (Gemini API key, SMTP credentials, storage keys) from injected secrets rather
than source.

#### Scenario: Bring up the platform
- **WHEN** the operator runs the Docker Compose deployment with required secrets provided
- **THEN** the pipeline, sound server, newsletter system, database, and storage start and can
  communicate

#### Scenario: Missing required secret
- **WHEN** a required secret is not provided at startup
- **THEN** the affected service fails fast with a clear error rather than starting in a
  broken state

### Requirement: VPS backend with a home GPU sound-worker
The system SHALL run all public and stateful services (website, pipeline, database, object
storage, newsletter, review dashboard) on an always-on VPS, and SHALL run voice generation on
a separate home GPU worker that connects out to the VPS to claim narration jobs — without the
home network exposing any inbound ports or requiring a static IP.

#### Scenario: Voice generation runs only on the home worker
- **WHEN** an episode needs narration
- **THEN** the work is performed by the home GPU worker, while all other services continue to
  run on the VPS

#### Scenario: Home worker offline does not affect the public site
- **WHEN** the home GPU worker is offline
- **THEN** the website, subscribe/opt-in flow, and newsletter sending remain fully available,
  and pending narration jobs queue on the VPS until the worker returns

#### Scenario: Worker connects without inbound exposure
- **WHEN** the home worker processes jobs
- **THEN** it authenticates and communicates with the VPS over an outbound connection only,
  with no inbound ports opened on the home network and no static IP required

#### Scenario: Cloned voice stays on the home machine
- **WHEN** the worker synthesizes narration
- **THEN** the reference voice sample and voice model remain on the home machine and are not
  uploaded to the VPS
