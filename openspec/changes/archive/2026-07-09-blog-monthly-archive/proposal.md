## Why

The blog listing page (`/blog` and `/en/blog`) renders every published post as one
flat reverse-chronological list. As the pipeline publishes more posts this becomes hard
to scan and gives visitors no sense of the archive's depth over time. Grouping posts by
month with a jump-to-month table of contents — the pattern used on akitaonrails.com, our
reference site — makes the archive navigable and signals a healthy publishing cadence.

## What Changes

- Group published blog posts by year + month on the listing page, under month headings
  (e.g. "2026 - July"), keeping reverse-chronological order within and across groups.
- Each month heading gets a stable anchor id (e.g. `2026---july`) so it can be linked to.
- Add a table-of-contents sidebar listing every month that has posts as anchor links that
  jump to the matching section on the page.
- Apply the grouping and TOC to both locales: PT at the site root and EN under `/en`,
  with localized month names and archive UI labels.
- Responsive: the sidebar collapses gracefully on narrow viewports; the grouped list
  remains fully usable without the sidebar.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `website`: The blog listing requirement gains month-grouped presentation and an
  archive table-of-contents; a new requirement covers the month grouping + anchored
  TOC navigation across both locales.

## Impact

- `web/src/components/PostList.astro` — group the already-sorted posts by `updated_at`
  year/month and render month headings with anchor ids.
- `web/src/pages/blog/index.astro` and `web/src/pages/en/blog/index.astro` — wrap the
  list in a two-column layout with the TOC sidebar.
- `web/src/styles/global.css` — grid/sidebar layout, sticky TOC, responsive collapse.
- `web/src/lib/i18n.js` — localized month names and archive UI strings (PT + EN).
- No data-layer change: posts already come from Postgres via `getPublishedPosts()`;
  grouping is derived at build time from `updated_at`. No new dependencies.
