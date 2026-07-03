## ADDED Requirements

### Requirement: Manual episodes support the same narration paths
Manually authored episodes SHALL support the same audio options as generated episodes: automatic
narration via the home GPU sound-worker for the primary language (pt-BR), and manual MP3 upload for
secondary languages (English).

#### Scenario: Auto-narrate a manual pt-BR episode
- **WHEN** the author requests narration for a manually authored pt-BR episode
- **THEN** a narration job is queued and the home sound-worker synthesizes and uploads the audio,
  just as for a generated episode

#### Scenario: Upload audio for a manual English episode
- **WHEN** the author uploads a recorded MP3 for a manually authored English episode
- **THEN** the system stores the audio and marks the episode ready, using the existing upload path

### Requirement: Manual episodes reuse episode audio state handling
A manually authored episode SHALL follow the same audio/status lifecycle as a generated one,
including re-narration keeping an already-published episode live.

#### Scenario: Re-narrate a published manual episode
- **WHEN** the author edits the script of a published manual episode and re-narrates it
- **THEN** the episode regenerates its audio and remains published and present in the podcast feed
