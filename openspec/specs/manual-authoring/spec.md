# Manual Authoring

## Purpose
Author-initiated content creation alongside the automated pipeline, entering the same review flow.

## Requirements

### Requirement: Hand-author a blog post
The system SHALL let a human author a blog post directly from the dashboard, providing a title
and Markdown body, without requiring an ingested/discovered topic.

#### Scenario: Create a post in one language
- **WHEN** the author submits a new post with a title and body for Portuguese
- **THEN** the system creates a blog draft for pt-BR in the review queue, backed by a manual
  topic, with no AI generation involved

#### Scenario: Create a post in both languages
- **WHEN** the author fills in the title and body for both Portuguese and English on the create
  form
- **THEN** the system creates one blog draft per language, each independently reviewable

#### Scenario: Optional newsletter blurb
- **WHEN** the author additionally provides a newsletter blurb for a language
- **THEN** the system also creates a newsletter draft for that language alongside the blog draft

### Requirement: Hand-author a podcast episode
The system SHALL let a human author a podcast episode directly from the dashboard, providing a
title, script, and show notes, in Portuguese and/or English, without requiring an ingested topic.

#### Scenario: Create an episode script
- **WHEN** the author submits a new episode with a title, script, and show notes for a language
- **THEN** the system creates an episode and a podcast draft for that language, ready for
  narration/audio and review

### Requirement: Manual content is first-class
Manually authored content SHALL flow through the same review, approval, publishing, and rendering
paths as automatically generated content, appearing on the site, RSS feed, and podcast feed
identically.

#### Scenario: Manual post goes live like a generated one
- **WHEN** a manually authored blog post is approved and published
- **THEN** it appears on the blog and in the RSS feed exactly as an AI-generated post would

#### Scenario: Manual episode appears in the podcast feed
- **WHEN** a manually authored episode is published and has audio
- **THEN** it appears in the podcast feed with an audio enclosure, like an auto-produced episode

### Requirement: No ingested topic required
The system SHALL create manually authored content without an ingested source topic, by attaching
it to a synthetic topic flagged as manually originated.

#### Scenario: Authoring without a discovered trend
- **WHEN** the author creates a post or episode that is unrelated to any discovered trend
- **THEN** the system provisions a manual-origin topic automatically and links the content to it,
  requiring no source URL or extracted article text

### Requirement: Optional author self-approval
The system SHALL let the author choose, at creation time, to save the content as a pending draft
or to approve it immediately.

#### Scenario: Save and approve in one step
- **WHEN** the author chooses "Save & approve" while creating content
- **THEN** the content is recorded as approved and becomes eligible for publishing without a
  separate review step

#### Scenario: Save as a pending draft
- **WHEN** the author chooses "Save as draft"
- **THEN** the content enters the review queue as pending and is not published until approved
