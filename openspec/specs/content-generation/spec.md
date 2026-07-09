# Content Generation

## Purpose
AI generation of blog posts and podcast scripts from discovered source material, in both PT and EN.

## Requirements

### Requirement: Multi-format generation from one topic
The system SHALL generate, from a single selected topic, a blog post (markdown with
frontmatter), a podcast script, and a newsletter blurb, all derived from the same extracted
source material.

#### Scenario: Generate all formats for a topic
- **WHEN** a topic is selected for generation
- **THEN** the system produces a blog draft, a podcast-script draft, and a newsletter-blurb
  draft, each linked to the originating topic

#### Scenario: One news item fans out to blog and podcast
- **WHEN** a single news item is approved for production
- **THEN** the resulting blog post and podcast episode are linked to the same topic so they
  can reference each other

### Requirement: Source-grounded generation
The system SHALL ground generated content in the extracted source articles and SHALL cite or
link the original sources in the output.

#### Scenario: Generation includes attribution
- **WHEN** content is generated for a topic
- **THEN** the output references the source articles used, and links to the originals are
  included in the blog post and show notes

### Requirement: Brand voice and format constraints
The system SHALL apply a configurable brand voice and per-format constraints (length, tone,
structure) when generating content.

#### Scenario: Per-format constraints applied
- **WHEN** content is generated
- **THEN** the blog post, podcast script, and newsletter blurb each conform to their
  configured length and structure for that channel

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
