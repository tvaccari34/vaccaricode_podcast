## Why

The first episode ("Welcome to Vaccari's Code Podcast" / "Bem-vindo…") explains
what the whole blog/newsletter/podcast is for. It's the ideal thing to greet a
first-time visitor, but today it's just one episode among many on `/podcast`,
sorted by date, and it appears nowhere on `/blog` or the home page (it is a
podcast-only topic — no blog post). As content grows it sinks out of sight.

## What Changes

- Add a **"Start here" featured card** pinned at the top of the home page, the
  blog listing, and the podcast listing. It links to the intro episode and shows
  its title and a short blurb.
- The pinned episode is identified by a configurable topic id (default: the
  welcome episode), resolved per language so PT and EN each link to their version.
- De-duplicate: the featured episode is removed from the normal episode list on
  the pages that show one (home, podcast), so it isn't listed twice. The blog
  list is unaffected (the intro is not a blog post).
- If the configured episode doesn't exist for a language, the card renders
  nothing (no error, no empty box).

## Impact

- `web/src/components/FeaturedIntro.astro` *(new)* — the card.
- `web/src/lib/featured.js` *(new)* — the featured topic id (env-overridable).
- `web/src/lib/db.js` — `getEpisodeByTopic(topicId, lang)` helper.
- `web/src/lib/i18n.js` — a localized "Start here" label.
- Listing pages (`index`, `blog/index`, `podcast/index` + their `/en` twins) —
  render the card and filter the featured item out of episode lists.
- `web/src/styles/global.css` — featured-card styling.
- Capability `website`: a new requirement for the pinned intro.
