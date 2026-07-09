# Review Workflow

## Purpose
The human approval queue and dashboard that gate generated drafts before anything goes live.

## Requirements

### Requirement: Approval gate before publishing
The system SHALL require human approval of generated content before it is published to any
channel.

#### Scenario: Unapproved content is not published
- **WHEN** content has been generated but not yet approved
- **THEN** it remains in a draft state and is not published to the blog, podcast, or
  newsletter

#### Scenario: Approval releases content to publishing
- **WHEN** a reviewer approves a draft for a channel
- **THEN** that content becomes eligible for publishing to the corresponding channel

### Requirement: Review dashboard
The system SHALL provide a dashboard where reviewers can see pending drafts with the blog
text, the newsletter blurb, and an audio preview of the podcast episode.

#### Scenario: Review a pending item
- **WHEN** a reviewer opens a pending item in the dashboard
- **THEN** they can read the blog and newsletter drafts and play the generated audio preview
  before deciding

### Requirement: Per-channel review decisions
The system SHALL let reviewers approve, reject, or request edits per channel, and SHALL
record who decided and when.

#### Scenario: Reject one channel, approve another
- **WHEN** a reviewer approves the blog post but rejects the newsletter blurb for the same
  topic
- **THEN** the blog becomes eligible to publish while the newsletter blurb does not, and both
  decisions are recorded with reviewer and timestamp

### Requirement: Management view alongside the review queue
The dashboard SHALL offer a content management view in addition to the pending-review queue, so the
owner can act on already-published content (which never appears in the review queue).

#### Scenario: Reach management from the dashboard
- **WHEN** the owner is on the dashboard
- **THEN** they can navigate to a management view listing all posts and episodes, separate from the
  pending-review queue

#### Scenario: Published content is actionable
- **WHEN** content has been published and therefore left the review queue
- **THEN** the owner can still edit, unpublish, regenerate audio, or delete it from the management
  view

### Requirement: Dashboard content-creation actions
The review dashboard SHALL provide "Create Post" and "Create Episode" actions that let a reviewer
author content by hand, in Portuguese and/or English.

#### Scenario: Open the create forms
- **WHEN** a reviewer is on the dashboard
- **THEN** they can open a "Create Post" form and a "Create Episode" form and choose the target
  language(s)

#### Scenario: Validation on create
- **WHEN** a reviewer submits a create form without a title or body for any selected language
- **THEN** the system rejects the submission and prompts for the missing fields

### Requirement: Manual drafts enter the same review queue
Manually authored drafts SHALL appear in the same review queue as generated drafts and support the
same per-channel approve / reject / request-edit decisions, recording who decided and when.

#### Scenario: Review a manual draft
- **WHEN** a reviewer opens the queue after a manual post is saved as a draft
- **THEN** the manual blog (and newsletter) draft appears with the same approve/reject/edit
  controls as generated drafts

#### Scenario: Manual and automated content coexist in the queue
- **WHEN** both manually authored and AI-generated drafts are pending
- **THEN** both are listed and independently reviewable, with neither mode hiding or overriding the
  other
