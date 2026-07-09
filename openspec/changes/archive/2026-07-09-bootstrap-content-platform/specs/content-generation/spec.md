## ADDED Requirements

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
