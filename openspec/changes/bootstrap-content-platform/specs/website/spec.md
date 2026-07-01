## ADDED Requirements

### Requirement: Static site with blog and podcast
The system SHALL provide a statically generated website (Astro) that presents blog posts and
podcast episodes from markdown content collections.

#### Scenario: Visitor browses the blog
- **WHEN** a visitor opens the site
- **THEN** they see a list of published blog posts and can open an individual post page

#### Scenario: Visitor browses podcast episodes
- **WHEN** a visitor opens the podcast section
- **THEN** they see published episodes with show notes and an embedded audio player

### Requirement: About / bio page
The system SHALL include an about page presenting Tiago Vaccari's bio.

#### Scenario: Visitor opens the about page
- **WHEN** a visitor opens the about page
- **THEN** they see Tiago's bio — Sr Software Engineer leading AI initiatives, 20+ years of
  experience, Brazilian origin, relocated from the UK to the US (Orlando, FL) in 2023 — with
  links to his GitHub and other profiles

### Requirement: Newsletter subscribe page
The system SHALL include a themed newsletter subscribe page integrated with the newsletter
system.

#### Scenario: Visitor subscribes from the site
- **WHEN** a visitor submits their email on the subscribe page
- **THEN** the submission is sent to the newsletter system to begin the opt-in flow, and the
  visitor sees a confirmation that they must confirm via email

### Requirement: Feeds and responsive theming
The system SHALL expose an RSS feed and the podcast feed from the site and SHALL render with
a responsive light/dark theme.

#### Scenario: Reader accesses the RSS feed
- **WHEN** a reader requests the site's RSS or podcast feed URL
- **THEN** a valid feed of published content is returned

#### Scenario: Theme toggle
- **WHEN** a visitor toggles between light and dark mode
- **THEN** the site renders in the selected theme
