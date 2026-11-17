# narration-provider Specification

## Purpose
Which narration backends the VPS supports (`local` home worker, `custom` HTTP model), how one is selected and validated at startup, the claim contract with the home worker (including the episode `language`), and when secondary-language episodes are narrated.
## Requirements
### Requirement: Supported narration providers
The pipeline SHALL accept `NARRATION_PROVIDER` values `local` (default) and `custom`, compared case-insensitively. Any other value, including the removed `elevenlabs`, MUST fail settings validation at startup, with an error that names the accepted values. The pipeline MUST NOT start with jobs that no component would drain.

#### Scenario: Default provider
- **WHEN** `NARRATION_PROVIDER` is unset
- **THEN** the provider is `local`, `/narration/claim` serves jobs to the home worker, and the VPS drainer does nothing

#### Scenario: Removed ElevenLabs provider
- **WHEN** the pipeline starts with `NARRATION_PROVIDER=elevenlabs`
- **THEN** startup fails with an error stating that `elevenlabs` is no longer supported and that the accepted values are `local` and `custom`

#### Scenario: Custom HTTP provider unchanged
- **WHEN** `NARRATION_PROVIDER=custom` and `CUSTOM_TTS_URL` is set
- **THEN** the VPS drainer synthesizes jobs through the custom HTTP provider exactly as before this change, and `/narration/claim` returns 204

### Requirement: ElevenLabs is not a narration backend
The codebase SHALL NOT contain an ElevenLabs provider, `ELEVENLABS_*` settings or ElevenLabs deployment instructions. Stray `ELEVENLABS_*` environment variables MUST be ignored without error.

#### Scenario: Leftover environment variables
- **WHEN** the production `.env` still contains `ELEVENLABS_API_KEY` and `NARRATION_PROVIDER=local`
- **THEN** the pipeline starts normally and never contacts `api.elevenlabs.io`

### Requirement: Claim response carries the episode language
`POST /narration/claim` SHALL return `id`, `episode_id`, `voice_id`, `text` and `language`. `language` is the claimed episode's language code, or `PRIMARY_LANGUAGE_CODE` when the episode has none. The new field MUST be additive, so that older workers that ignore it keep working.

#### Scenario: Secondary-language episode
- **WHEN** the next queued job belongs to an episode with `language=en`
- **THEN** the claim response includes `"language": "en"`

#### Scenario: Episode without a language
- **WHEN** the next queued job belongs to an episode whose `language` is null
- **THEN** the claim response includes `"language"` equal to `PRIMARY_LANGUAGE_CODE`

### Requirement: Secondary-language narration on the home worker
`NARRATION_SECONDARY_ENABLED=true` SHALL queue narration jobs for secondary-language episodes under every provider, including `local`, and the home worker SHALL narrate them in the secondary-language voice.

#### Scenario: English auto-narration with the local provider
- **WHEN** `NARRATION_PROVIDER=local`, `NARRATION_SECONDARY_ENABLED=true` and the podcast drafts of a bilingual post are approved
- **THEN** two narration jobs are queued, one per language, and each is claimable by the home worker with its own `language`

#### Scenario: Dashboard narration controls for the secondary language
- **WHEN** `NARRATION_SECONDARY_ENABLED=true`
- **THEN** the dashboard offers edit-script & re-narrate for secondary-language episodes (alongside the manual MP3 upload), and Create Episode can queue secondary-language narration
- **AND** when it is `false`, secondary-language episodes offer only the manual MP3 upload, as before

