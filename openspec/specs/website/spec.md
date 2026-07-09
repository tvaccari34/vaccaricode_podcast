# Website

## Purpose
The public Astro site (blog, podcast, about, subscribe): listing, month-grouped archive presentation, and localization.

## Requirements

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

### Requirement: Blog listing grouped by month
The blog listing page SHALL group published posts by the year and month of their
publication date (`updated_at`), presenting each group under a month heading formatted as
"YYYY - MonthName" (e.g. "2026 - July"). Groups SHALL appear in reverse-chronological
order (most recent month first), and posts within a group SHALL remain in
reverse-chronological order. Each month heading SHALL carry a stable, unique anchor id
derived from the group (e.g. `2026---july`). This grouping SHALL apply to both the PT
listing at the site root and the EN listing under `/en`, using locale-appropriate month
names.

#### Scenario: Visitor sees posts grouped under month headings
- **WHEN** a visitor opens the blog listing page and posts exist across multiple months
- **THEN** the posts appear beneath month headings ordered most-recent-month first, with
  each post listed under the heading for the month of its publication date

#### Scenario: Month heading exposes a linkable anchor
- **WHEN** the listing renders a month group
- **THEN** the month heading has a stable anchor id, and navigating to that anchor scrolls
  the page to that month's section

#### Scenario: Localized month names per locale
- **WHEN** a visitor opens the EN listing under `/en` versus the PT listing at the root
- **THEN** each month heading is rendered with the month name in that locale's language

### Requirement: Blog archive table-of-contents navigation
The blog listing page SHALL present a table-of-contents that lists every month containing
at least one published post, in reverse-chronological order, as anchor links that jump to
the corresponding month section on the same page. The table-of-contents SHALL be rendered
in both locales with localized labels. The listing SHALL remain fully usable — every post
reachable — when the table-of-contents is not shown (e.g. on narrow viewports).

#### Scenario: Visitor jumps to a month via the table-of-contents
- **WHEN** a visitor clicks a month entry in the table-of-contents
- **THEN** the page scrolls to that month's section in the listing

#### Scenario: Table-of-contents reflects only months with posts
- **WHEN** the listing has posts in some months but not others
- **THEN** the table-of-contents lists only the months that contain at least one post

#### Scenario: Listing usable without the table-of-contents
- **WHEN** a visitor views the listing on a narrow viewport where the sidebar is collapsed
  or hidden
- **THEN** all month groups and posts remain visible and scrollable in the main column

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
