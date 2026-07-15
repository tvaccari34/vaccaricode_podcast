## ADDED Requirements

### Requirement: Editorial lane classification
The system SHALL classify every candidate topic into exactly one of four editorial lanes —
`business-story` (a business story with a lesson learned), `business-problem` (a business
problem solved), `tech-deepdive` (AI, automation, or data analysis), and `bigtech-news`
(news about Big Tech) — and SHALL persist the assigned lane on the topic. Classification MAY
use the language model, with a deterministic fallback (e.g. source hint or keywords) when the
model is unavailable, and SHALL always yield exactly one lane per topic.

#### Scenario: Topic is assigned a lane
- **WHEN** a candidate topic is scored/prepared for selection
- **THEN** it is assigned exactly one of the four lanes, and that lane is stored on the topic

#### Scenario: Classification fallback
- **WHEN** the language model is unavailable or returns no usable lane
- **THEN** the topic still receives exactly one lane via the deterministic fallback, and the
  run continues

### Requirement: Lane-oriented sources
The system SHALL support sources that feed the business and Big Tech lanes (not only
developer-centric sources), so that every lane has candidate topics to draw from.

#### Scenario: Business-lane candidates exist
- **WHEN** the ingestion job runs with the configured sources
- **THEN** candidates are produced for the business and Big Tech lanes, not only the technical
  lane

### Requirement: Lane-balanced selection
When selecting which topics to generate, the system SHALL balance across the four lanes over a
rolling window rather than choosing by global score alone, while still preferring higher-scored
topics *within* each lane. No single lane SHALL dominate the published output over that window.

#### Scenario: Balanced pick across lanes
- **WHEN** the system selects the next batch of topics to generate and multiple lanes have
  candidates
- **THEN** the selection distributes across the four lanes per the configured balance, rather
  than taking only the globally top-scored topics

#### Scenario: Highest score wins within a lane
- **WHEN** a lane is allotted a slot in the selection
- **THEN** the highest-scored not-yet-used candidate in that lane is chosen

#### Scenario: A lane has no candidates
- **WHEN** a lane has no available candidates for the current window
- **THEN** its slot is reallocated to other lanes so throughput is not blocked, and the
  shortfall is recorded so balance can recover in later windows
