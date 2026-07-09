## ADDED Requirements

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
