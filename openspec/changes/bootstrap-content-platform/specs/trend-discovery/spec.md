## ADDED Requirements

### Requirement: Scheduled multi-source trend ingestion
The system SHALL ingest candidate topics from multiple configured IT/software-development
sources (RSS/Atom feeds, Hacker News, GitHub Trending, and similar aggregators) on a
configurable schedule.

#### Scenario: Scheduled ingestion run
- **WHEN** the ingestion job runs on its schedule
- **THEN** each enabled source is fetched, and new items are stored as raw candidate topics
  with source, URL, title, timestamp, and fetched-at metadata

#### Scenario: A source is unavailable
- **WHEN** one source fails to respond or returns an error
- **THEN** the run logs the failure, continues with the remaining sources, and still
  persists the candidates it successfully fetched

### Requirement: Article extraction
The system SHALL extract clean, readable article text from each candidate's source URL for
later grounding of generated content.

#### Scenario: Extract readable content
- **WHEN** a candidate topic has a reachable source URL
- **THEN** the main article text is extracted (boilerplate removed) and stored with the
  candidate for use as generation context

### Requirement: Deduplication and scoring
The system SHALL deduplicate near-identical candidates and assign each a relevance score so
the most significant trends surface first.

#### Scenario: Duplicate stories across sources
- **WHEN** the same story appears from more than one source within the dedup window
- **THEN** the candidates are merged into a single topic that records all contributing
  sources

#### Scenario: Ranking the candidate queue
- **WHEN** candidates are scored
- **THEN** the candidate queue is ordered by relevance score so reviewers see the strongest
  trends at the top
