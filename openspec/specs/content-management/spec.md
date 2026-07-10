# Content Management

## Purpose
Managing the lifecycle and state of content items (topics, drafts) across channels in the database.

## Requirements

### Requirement: Content management view
The dashboard SHALL provide a management view listing all blog posts and podcast episodes, in
Portuguese and English, showing each item's language and current status regardless of whether it is
published. The view SHALL separate content that still needs action from already-published content
(see "Management view organization and filtering").

#### Scenario: See all posts and episodes
- **WHEN** the owner opens the management view
- **THEN** they see every blog post and every episode — including both automated and manually
  authored content — each with its language and status (e.g. pending, ready, published)
### Requirement: Publish and unpublish an item
The owner SHALL be able to publish a specific post or episode, and to unpublish a published one so
it is removed from the public site and feeds.

#### Scenario: Unpublish a live post
- **WHEN** the owner unpublishes a published blog post
- **THEN** the post is no longer served on the site or RSS feed after the next site rebuild, while
  remaining stored and editable

#### Scenario: Publish an item directly
- **WHEN** the owner publishes a specific post or episode from the management view
- **THEN** that item becomes published and is served on the site/feed after the next rebuild

### Requirement: Edit a post or episode
The owner SHALL be able to edit a post's title and body, and an episode's title, script, and show
notes, from the management view.

#### Scenario: Edit a published post's text
- **WHEN** the owner edits the body of a published post and saves
- **THEN** the updated text is shown on the live site after the next rebuild, and the post stays
  published

### Requirement: Regenerate episode audio
The owner SHALL be able to regenerate an episode's audio from the management view — re-narrate it
(pt-BR home worker) or upload a new MP3.

#### Scenario: Re-narrate from the management view
- **WHEN** the owner triggers re-narration for an episode
- **THEN** a new narration job is queued and the episode's audio is replaced when the worker
  completes, keeping a published episode live

### Requirement: Delete a post or episode
The owner SHALL be able to delete a post or an episode; deleting an episode SHALL also remove its
stored audio object(s).

#### Scenario: Delete an episode
- **WHEN** the owner deletes an episode
- **THEN** the episode is removed from the site/feed after the next rebuild and its stored audio
  object(s) are purged from object storage

#### Scenario: Delete does not affect sibling content
- **WHEN** the owner deletes one blog post that shares a topic with an episode or the other-language
  post
- **THEN** only that post is removed and the sibling content is left intact

### Requirement: Destructive actions are confirmed
The system SHALL require an explicit confirmation before deleting or unpublishing content.

#### Scenario: Confirm before delete
- **WHEN** the owner clicks delete on a post or episode
- **THEN** they must confirm the action before it is carried out

### Requirement: Management view organization and filtering
The management view SHALL present unpublished (in-progress) items ahead of published items, so the
owner can act on pending content without scrolling past the live archive, and SHALL keep the
published items available but collapsed by default with a visible count. The view SHALL provide
client-side controls to narrow the listed items by language (all / Portuguese / English) and by a
free-text title query, updating live without a page reload. No item SHALL be permanently hidden —
every item remains reachable through these controls.

#### Scenario: Actionable content is surfaced first
- **WHEN** the owner opens the management view with a mix of unpublished and published content
- **THEN** the unpublished items appear first, and the published items are shown under a collapsed,
  counted section

#### Scenario: Filter by language
- **WHEN** the owner selects a single language in the language filter
- **THEN** only items in that language remain visible, and choosing "all" restores every item

#### Scenario: Filter by title
- **WHEN** the owner types text into the title filter
- **THEN** only items whose title contains that text remain visible, updating as they type, and any
  matching published items are revealed by expanding the collapsed section

#### Scenario: Published content keeps its actions
- **WHEN** the owner expands the collapsed published section
- **THEN** every published item is listed with the same per-item actions as before (unpublish, edit,
  upload audio, delete), each still confirming destructive actions
