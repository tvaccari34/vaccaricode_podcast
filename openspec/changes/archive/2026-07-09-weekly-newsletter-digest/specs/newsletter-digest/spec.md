## ADDED Requirements

### Requirement: Weekly digest aggregates the week's posts
The system SHALL produce a weekly newsletter digest that aggregates the posts published in the last
7 days into a single campaign per language, with one section per post.

#### Scenario: A week with several posts
- **WHEN** the weekly digest runs and several posts were published in the window for a language
- **THEN** the system creates exactly one Listmonk campaign for that language whose body contains a
  section (title, blurb, and link) for each of those posts

#### Scenario: Separate digest per language
- **WHEN** posts were published in both Portuguese and English in the window
- **THEN** the system creates one campaign per language, each targeting that language's list

### Requirement: No duplicate posts across digests
The system SHALL NOT include a post in more than one digest.

#### Scenario: Running the digest twice
- **WHEN** the digest runs, and then runs again before any new post is published
- **THEN** the second run creates no campaign because there are no new posts since the last digest

### Requirement: Empty week sends nothing
The system SHALL NOT create a campaign for a language that had no posts published in the window.

#### Scenario: No new posts
- **WHEN** the digest runs for a language with no posts published since the last digest
- **THEN** no campaign is created and no digest is recorded for that language

### Requirement: Digest is created as a draft unless auto-send is enabled
The digest SHALL create the campaign as a draft for review by default, and SHALL send it
automatically only when auto-send is explicitly enabled.

#### Scenario: Default review-before-send
- **WHEN** the digest creates a campaign and auto-send is disabled
- **THEN** the campaign is left as a draft for a human to review and send

#### Scenario: Auto-send enabled
- **WHEN** the digest creates a campaign and auto-send is enabled
- **THEN** the campaign is started so it is delivered to subscribers without manual action

### Requirement: Weekly schedule
The digest SHALL be runnable on a weekly schedule and on demand.

#### Scenario: Scheduled weekly run
- **WHEN** the weekly schedule fires
- **THEN** the digest runs for all configured languages and reports what it created
