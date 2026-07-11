## 1. Data + config

- [x] 1.1 Add `web/src/lib/featured.js` exporting `FEATURED_TOPIC_ID` (default = the welcome episode topic id; overridable via `PUBLIC_FEATURED_TOPIC_ID`).
- [x] 1.2 Add `getEpisodeByTopic(topicId, language)` to `web/src/lib/db.js` returning one published episode row (or null).
- [x] 1.3 Add a localized `startHere` label to `web/src/lib/i18n.js` (PT + EN).

## 2. Component

- [x] 2.1 Add `web/src/components/FeaturedIntro.astro`: fetch the featured episode for `lang`; render a "start here" card (label + title + short blurb) linking to `/podcast/<id>`; render nothing if absent.
- [x] 2.2 Add featured-card styles to `web/src/styles/global.css`.

## 3. Wire into landing pages

- [x] 3.1 Home (`index.astro` + `en/index.astro`): render the card after the hero; filter the featured topic out of the episode list.
- [x] 3.2 Blog (`blog/index.astro` + `en/blog/index.astro`): render the card above the archive.
- [x] 3.3 Podcast (`podcast/index.astro` + `en/podcast/index.astro`): render the card above the list; filter the featured topic out of the list.

## 4. Verification

- [x] 4.1 DB-backed build: confirm the card renders on all three pages in PT and EN, links to the right per-language episode, and the episode is not duplicated in the lists.
- [x] 4.2 Confirm graceful absence (bad id → no card, page intact).
