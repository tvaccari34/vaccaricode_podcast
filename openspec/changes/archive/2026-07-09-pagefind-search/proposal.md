## Why

The site has no search — as the automated pipeline keeps publishing, readers can only
browse the reverse-chronological listing (now month-grouped) with no way to find a post by
keyword. Our reference site (akitaonrails.com) ships client-side search via its Hextra
theme; we hand-roll our UI and have nothing equivalent. Pagefind is the Astro-native fit: it
indexes the built static HTML and runs entirely in the browser — no server and no database
at query time, preserving our static-delivery model.

## What Changes

- Add **Pagefind** as a build-time indexer: after `astro build`, index `dist/` into a static
  `/pagefind/` bundle (build script becomes `astro build && pagefind --site dist`).
- Add a **search entry in the header** (mirroring akita's "Buscar"/"Search" nav item) that
  opens a **keyboard-accessible modal** (click or Ctrl-/Cmd-K), available from any page.
- Search results render inline in the modal as the user types, styled to the neon theme,
  each result showing title, a matching excerpt, and a **content-type tag (Blog / Podcast)**.
- **Index blog posts and podcast episodes**: mark each page's main content region with
  `data-pagefind-body` (and exclude chrome — header/nav/footer) so only real content is
  indexed; capture title + excerpt + type for result cards.
- **Bilingual by construction**: Pagefind segments indexes by the page's `<html lang>`
  (`pt-BR` vs `en`), so PT and EN searches only return same-language results. Add localized
  search UI strings (placeholder, "no results", open/close labels) to `i18n.js` for both.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `website`: gains a site-search requirement — a client-side, per-language search over
  published blog posts and podcast episodes, reachable from every page.

## Impact

- `web/package.json` — add `pagefind` devDependency; update the `build` script to run
  Pagefind after `astro build`.
- `web/src/layouts/Base.astro` — header search trigger + the search modal markup/behavior;
  ensure `<html lang>` is present for Pagefind language segmentation (already set).
- `web/src/components/PostArticle.astro` and `web/src/components/EpisodeArticle.astro`
  (or the article containers) — add `data-pagefind-body` to the content region and
  `data-pagefind-meta` for the content-type tag; keep chrome out of the index.
- `web/src/lib/i18n.js` — localized search strings (PT + EN).
- `web/src/styles/global.css` — modal + results styling in the neon theme.
- Build/deploy: the Docker/VPS build step must install `pagefind` and produce the
  `/pagefind/` bundle; the static output now includes it. No runtime service, no DB at query
  time.
- Out of scope: decoupling the build from Postgres (separate change), search analytics,
  server-side search.
