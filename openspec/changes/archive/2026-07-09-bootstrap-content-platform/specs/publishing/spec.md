## ADDED Requirements

### Requirement: Publish approved blog posts
The system SHALL publish approved blog posts to the website as markdown content with
frontmatter, triggering a site rebuild/deploy.

#### Scenario: Approved blog post goes live
- **WHEN** a blog post is approved for publishing
- **THEN** its markdown file is written to the site's content collection and the site is
  rebuilt so the post is publicly visible

### Requirement: Publish podcast episodes to a feed
The system SHALL publish approved episodes to an iTunes/Apple-compatible podcast RSS feed
that references the audio file in object storage.

#### Scenario: Episode appears in the podcast feed
- **WHEN** an episode is approved for publishing
- **THEN** the podcast RSS feed includes an item with the episode's title, show notes,
  duration, and enclosure URL, and a matching episode page is published on the site

### Requirement: Send approved newsletter editions
The system SHALL send approved newsletter content to subscribers via the newsletter system.

#### Scenario: Newsletter edition is sent
- **WHEN** a newsletter edition is approved for sending
- **THEN** a campaign is created and delivered to the active subscriber list through the
  configured sending provider

### Requirement: Feed generation
The system SHALL generate and keep current a blog RSS feed and the podcast feed as content is
published.

#### Scenario: Feeds reflect latest content
- **WHEN** new blog or podcast content is published
- **THEN** the corresponding RSS/podcast feed is regenerated to include the latest items
