## ADDED Requirements

### Requirement: Per-lane subscribe attribution
The system SHALL tag off-site newsletter/subscribe call-to-action links (podcast show notes and
newsletter) with a campaign value that includes the topic's editorial lane, so subscriptions can
be attributed to the lane that drove them. On-site links MAY remain untagged.

#### Scenario: CTA link carries the lane
- **WHEN** a subscribe CTA is generated for a topic delivered off-site
- **THEN** the link's campaign/UTM tag includes the topic's lane

#### Scenario: Attribution by lane
- **WHEN** subscriptions arrive via tagged CTA links across topics
- **THEN** each subscription's campaign tag identifies the lane, allowing list growth to be
  compared across the four lanes
