## ADDED Requirements

### Requirement: Per-item publish and unpublish
The system SHALL support publishing and unpublishing an individual post or episode, independently of
the topic-wide publish of approved drafts.

#### Scenario: Publish a single item
- **WHEN** an owner publishes one specific post or episode
- **THEN** only that item is marked published and recorded as a publication, without requiring the
  whole topic to be processed

#### Scenario: Unpublish returns an item to a non-public state
- **WHEN** an owner unpublishes a published item
- **THEN** the item's status is set back to a non-published state so the site build no longer
  includes it, while the content is retained

### Requirement: Delete removes content from all channels
Deleting a post or episode SHALL remove it from the site and feeds and SHALL clean up associated
artifacts (an episode's stored audio and its narration jobs).

#### Scenario: Deleted episode leaves no orphaned audio
- **WHEN** an episode is deleted
- **THEN** its audio object(s) in storage are removed and its narration jobs no longer exist
