## ADDED Requirements

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
