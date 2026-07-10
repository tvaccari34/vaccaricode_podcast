## MODIFIED Requirements

### Requirement: Content management view
The dashboard SHALL provide a management view listing all blog posts and podcast episodes, in
Portuguese and English, showing each item's language and current status regardless of whether it is
published. The view SHALL separate content that still needs action from already-published content
(see "Management view organization and filtering").

#### Scenario: See all posts and episodes
- **WHEN** the owner opens the management view
- **THEN** they see every blog post and every episode — including both automated and manually
  authored content — each with its language and status (e.g. pending, ready, published)

## ADDED Requirements

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
