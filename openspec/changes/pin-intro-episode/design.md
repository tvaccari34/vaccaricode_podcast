## Context

Listing pages are static Astro pages that query Postgres at build time via
`web/src/lib/db.js` and render components (`EpisodeList`, `PostList`). Episodes
and posts are ordered `updated_at DESC`; there is no "featured" concept. The
intro is a podcast-only topic (`901bce52-…`): it has published episodes in PT and
EN but no `channel='blog'` draft, so it shows on `/podcast` only. The home page
and podcast page both render an episode list; the blog page does not.

## Decisions

### Identify the pinned item by topic id, resolved per language
A single `FEATURED_TOPIC_ID` (in `web/src/lib/featured.js`, overridable via
`PUBLIC_FEATURED_TOPIC_ID`) names the topic. The card fetches that topic's
episode for the current language with a new `getEpisodeByTopic(topicId, lang)`
query, so PT links to `/podcast/<id>` and EN to `/en/podcast/<id>`. Using the
topic id (not a hard-coded URL) keeps PT/EN correct and lets the pin move by
changing one value.

### Card, not a re-sort
Rather than hacking sort order (which would fight the blog's month grouping and
only work where the item is in the list), the intro is surfaced as a distinct
"Start here" card above the listing. This works uniformly on all three pages,
including the blog where the intro isn't part of the list at all.

### De-duplicate in the page, not the query
Pages that render an episode list (home, podcast) filter out `FEATURED_TOPIC_ID`
before passing episodes to `EpisodeList`, so the pinned item isn't shown twice.
`getPublishedEpisodes` stays generic (still used by feeds/sitemap unchanged).

### Graceful absence
`getEpisodeByTopic` returns null when the topic has no episode in that language;
`FeaturedIntro` renders nothing in that case, so a bad/blank id can't break a page.

## Risks / Trade-offs

- The featured id is config, not data-driven "is_featured" — fine for a single,
  rarely-changing intro; a DB flag would be overkill.
- The card duplicates a bit of episode-card markup; acceptable for a distinct
  visual treatment ("Start here" pill, blurb) that shouldn't drift with the list.
