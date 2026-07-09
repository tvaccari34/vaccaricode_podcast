## ADDED Requirements

### Requirement: Client-side site search
The site SHALL provide a client-side search over published content that runs entirely in the
browser against a statically generated index (no server and no database at query time). The
index SHALL be produced at build time from the generated HTML and SHALL cover published blog
posts and podcast episodes. Search SHALL be reachable from every page via a control in the
site header.

#### Scenario: Reader opens search from any page
- **WHEN** a reader activates the header search control (by click or the keyboard shortcut)
- **THEN** a search input opens with focus, allowing a query to be entered without leaving
  the current page

#### Scenario: Reader finds a post by keyword
- **WHEN** a reader types a query that matches a published blog post or podcast episode
- **THEN** matching results appear showing the title, a matching excerpt, and a content-type
  indicator (blog or podcast), and selecting a result navigates to that page

#### Scenario: No matches
- **WHEN** a reader types a query with no matching content
- **THEN** a localized "no results" message is shown rather than an empty or broken state

#### Scenario: Search index excludes site chrome
- **WHEN** the search index is built from the site output
- **THEN** it indexes only the main content of post and episode pages, not the header,
  navigation, footer, or listing-page chrome

### Requirement: Per-language search results
Search SHALL return results only in the language of the page the reader is searching from,
so that a reader on the Portuguese site does not see English results and vice versa. Search
UI labels SHALL be localized for both locales.

#### Scenario: Portuguese search stays Portuguese
- **WHEN** a reader searches from the Portuguese site (root)
- **THEN** only Portuguese-language content is returned, and the search UI labels are in
  Portuguese

#### Scenario: English search stays English
- **WHEN** a reader searches from the English site (under `/en`)
- **THEN** only English-language content is returned, and the search UI labels are in English
