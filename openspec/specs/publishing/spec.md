# Publishing

## Purpose
Rendering approved content to the public site, feeds, and newsletter, and keeping them in sync on each rebuild.

## Requirements

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

### Requirement: Publishing does not email subscribers per post
Publishing an individual post SHALL NOT create or send a newsletter campaign. Publishing SHALL
still release the post's blog/podcast/newsletter content and record its publications; the weekly
digest is the only thing that creates newsletter campaigns.

#### Scenario: Publishing a single post
- **WHEN** a post is published (manually or by the pipeline)
- **THEN** its content goes live and its publications are recorded, but no Listmonk campaign is
  created for that post

#### Scenario: The newsletter blurb remains available to the digest
- **WHEN** a post with an approved newsletter blurb is published
- **THEN** the blurb is stored and later included as that post's section in the weekly digest

### Requirement: Feed generation
The system SHALL generate and keep current a blog RSS feed and the podcast feed as content is
published.

#### Scenario: Feeds reflect latest content
- **WHEN** new blog or podcast content is published
- **THEN** the corresponding RSS/podcast feed is regenerated to include the latest items

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
