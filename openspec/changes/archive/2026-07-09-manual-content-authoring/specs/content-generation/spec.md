## ADDED Requirements

### Requirement: Automated generation excludes manually authored content
The automated pipeline (scoring, topic selection, and generation) SHALL ignore manual-origin
topics, so hand-written content is never regenerated, scored, or overwritten by the AI pipeline.

#### Scenario: Generation skips manual topics
- **WHEN** the generate step selects the next topic to produce content for
- **THEN** it only considers auto-origin topics and never selects a manual-origin topic

#### Scenario: Manual content survives pipeline runs
- **WHEN** the ingest / extract / generate / scoring jobs run while manual drafts or episodes exist
- **THEN** the manual content and its topic are left unchanged

### Requirement: Both authoring modes coexist
The system SHALL support automated generation and manual authoring simultaneously; enabling manual
authoring SHALL NOT disable or degrade the automated trend → AI pipeline.

#### Scenario: Pipeline keeps running alongside manual content
- **WHEN** the automated pipeline is scheduled and manual content also exists
- **THEN** the pipeline continues to discover, generate, and publish auto content normally
