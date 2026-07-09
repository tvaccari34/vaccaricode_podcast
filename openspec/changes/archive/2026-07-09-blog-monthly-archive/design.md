## Context

The blog listing pages (`web/src/pages/blog/index.astro` for PT, `web/src/pages/en/blog/index.astro`
for EN) call `getPublishedPosts(lang)` from `web/src/lib/db.js`, which returns rows
`{ topic_id, title, body, updated_at }` already ordered `updated_at DESC`. They pass the
array to `web/src/components/PostList.astro`, which renders a flat `<ul class="bare">` of
`<li class="card">` items with a `.meta` date line. Styling is hand-written CSS in
`web/src/styles/global.css` (no theme framework; `.wrap { max-width: var(--maxw) }` centers
content). Localized strings live in `web/src/lib/i18n.js` (`STRINGS`, `href(lang, path)`);
PT is served at the root and EN under `/en`. The site is Astro 5 static output — all
grouping is computed at build time, so there is no client-side data cost.

This change is UI-only: group the already-sorted posts by month, render month headings with
anchors, and add a table-of-contents sidebar. akitaonrails.com is the reference pattern
(month headings + a sticky TOC of `#YYYY---monthname` anchors).

## Goals / Non-Goals

**Goals:**
- Group the blog listing by year+month with reverse-chronological month headings.
- Give each month a stable anchor id and a TOC entry that jumps to it.
- Work identically in PT (root) and EN (`/en`) with localized month names/labels.
- Keep the listing fully usable when the sidebar is hidden (narrow viewports).
- No data-layer or dependency changes.

**Non-Goals:**
- No web archive of the email newsletter (that content is not rendered to the web).
- No per-year collapsing, pagination, tag/category facets, or search.
- No change to individual post pages or to the podcast listing.
- No new DB query or SQL-side aggregation (grouping is derived in the component).

## Decisions

### Group in the component from `updated_at`, not in SQL
The rows are already sorted `updated_at DESC`, so a single pass groups them into
`[{ year, month, key, label, posts }]` preserving order. Keeping this in
`PostList.astro` (or a small helper it imports) avoids a second DB round-trip and keeps the
data layer unchanged. Alternative — a `GROUP BY date_trunc('month', updated_at)` query for
counts — was rejected as unnecessary complexity for a build-time list we already fetch in full.

### Anchor id derivation matches the reference pattern
Anchor id = lowercased `"{year}---{monthname-en}"` (e.g. `2026---july`), mirroring
akitaonrails. Using the English month name for the *id* keeps anchors stable and
URL-clean regardless of the page locale, while the *visible* heading uses the localized
month name. The id is computed from the year/month numbers, not string-parsed from the
label, so it stays stable if label formatting changes.

### Localized month names via i18n, not `toLocaleDateString`
Add an explicit ordered month-name array per locale to `web/src/lib/i18n.js` (PT + EN) and
an archive label string (e.g. TOC heading). Relying on `Date.prototype.toLocaleString`
with a locale depends on the build host's ICU/locale data; an explicit array is
deterministic across build environments and consistent with how the project already
centralizes copy in `i18n.js`.

### Layout: CSS grid with the list first in the DOM
The listing page becomes a two-column CSS grid (main list + aside TOC). The main list is
placed first in source order so that with the sidebar hidden (single-column at narrow
widths) content reads naturally and remains fully navigable; the TOC is `position: sticky`
on wide viewports and collapses (hidden or stacked) below a breakpoint. This is added to
`global.css` alongside the existing `.wrap`/`.card` rules rather than introducing a CSS
framework.

### Shared grouping helper to avoid PT/EN drift
The grouping logic is written once (helper used by `PostList.astro`) and both locale pages
pass their `lang`, so PT and EN cannot diverge in ordering/anchor logic — only the
localized labels differ.

## Risks / Trade-offs

- Empty/sparse archive (only one month of posts) → the TOC shows a single entry and the
  grouping still renders correctly; acceptable, no special-casing needed.
- `updated_at` (not front-matter `date`) drives grouping → a post edited later could hop
  months. Mitigation: acceptable for a listing/archive view; matches the current `.meta`
  date already shown from `updated_at`, so behavior is consistent with today.
- Sticky sidebar vs. long month sections → mitigate with `position: sticky; top` and a
  max-height/overflow on the TOC so it never overflows the viewport.
- Anchor collisions if two groups map to the same id → impossible since id is
  year+month-unique; still assert uniqueness when building the group list.
- Localized month arrays can fall out of sync with new locales → only PT/EN exist today;
  the helper reads from the same `STRINGS` source, so adding a locale is a single edit.

## Open Questions

- Should the visible heading be "2026 - July" (space-hyphen-space, matching akitaonrails)
  or a more locale-natural form (e.g. "Julho de 2026" in PT)? Default: mirror the
  reference format "YYYY - Month" in both locales for visual parity; revisit if the PT
  wording feels unnatural.
- Should the TOC be hidden entirely on mobile or stacked above the list? Default: hide
  below the breakpoint (list already carries the same month headings inline).
