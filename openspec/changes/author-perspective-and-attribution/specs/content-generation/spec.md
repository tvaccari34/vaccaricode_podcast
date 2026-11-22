## ADDED Requirements

### Requirement: Attribution of first-person source content
The system SHALL instruct generation (blog, podcast script and newsletter blurb) to report
first-person experiences, results, quotes and decisions found in the source material in the third
person, credited to the source's author or publisher, and SHALL NOT present them as the host's own.
This rule SHALL be part of every per-format prompt so it applies even when the brand voice is
overridden.

#### Scenario: Source author's experience is credited, not claimed
- **WHEN** a topic's source article describes the author's own experience in the first person
- **THEN** the generation prompt for each format instructs the model to describe that experience
  as the source author's or publisher's, in the third person, and never as something the host did

#### Scenario: Rule survives a brand-voice override
- **WHEN** `BRAND_VOICE` is set to a custom voice
- **THEN** the per-format generation prompts still contain the perspective and attribution rule

#### Scenario: Publishers are available for attribution
- **WHEN** the source material block is assembled for a topic with source URLs
- **THEN** it includes the publishers of the sources (the unique URL hosts, without `www.`), so
  the model has a name to credit

### Requirement: Host perspective and author profile
The system SHALL use the host's voice for analysis, opinion and practical takeaways only. It SHALL
draw the host's personal experiences, background and recurring opinions only from a configured
author profile, and SHALL NOT invent them. The author profile SHALL be optional, read from a file
(`AUTHOR_PROFILE_FILE`) or from env text (`AUTHOR_PROFILE`), and re-read on each generation so
edits apply without a redeploy.

#### Scenario: Profile informs the host's perspective
- **WHEN** an author profile file exists and is non-empty and content is generated
- **THEN** the generation system instruction includes the profile as the only allowed source of
  the host's own experiences and opinions

#### Scenario: No profile means no invented anecdotes
- **WHEN** no author profile is configured and content is generated
- **THEN** generation still succeeds, and the prompt forbids claiming personal experiences, past
  projects, employers or numbers about the host

#### Scenario: Profile edits apply on the next generation
- **WHEN** the author profile file is edited between two generations
- **THEN** the second generation uses the edited profile without a restart or redeploy

#### Scenario: Oversized profile is bounded
- **WHEN** the author profile exceeds the configured size limit
- **THEN** it is truncated to the limit and a warning is logged, and generation proceeds
