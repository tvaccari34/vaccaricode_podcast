## Context

The site is Astro 5 static output; pages are built from Postgres at build time and served as
plain HTML/CSS/JS with no runtime backend. Individual content pages render through
`web/src/components/PostArticle.astro` and `web/src/components/EpisodeArticle.astro`, both of
which wrap their content in a single `<article>` element inside `Base.astro`'s
header/nav/footer chrome. `Base.astro` already sets `<html lang>` to `pt-BR` (root) or `en`
(`/en`). Styling is hand-written neon CSS in `web/src/styles/global.css`; UI copy is
centralized in `web/src/lib/i18n.js`. akitaonrails.com (our reference) offers client-side
search via the Hextra theme; we have none.

Pagefind is the Astro-recommended static search: a CLI that indexes built HTML into a
same-origin `/pagefind/` bundle, plus a browser library that queries it client-side. This
keeps search consistent with our static-delivery model — no server, no DB at query time.

## Goals / Non-Goals

**Goals:**
- Client-side search over published blog posts and podcast episodes, reachable from every page.
- Keyboard-accessible modal (click or Ctrl/Cmd-K) styled to the neon theme; results show
  title, excerpt, and a Blog/Podcast type tag.
- Per-language results (PT vs EN) with no cross-language leakage; localized UI strings.
- Index only real content, not header/nav/footer/listing chrome.
- No runtime service and no database at query time.

**Non-Goals:**
- Decoupling the Astro build from Postgres (tracked separately).
- Search analytics / query logging.
- Server-side or full-text-DB search.
- Fuzzy tuning, synonyms, or ranking customization beyond Pagefind defaults.

## Decisions

### Pagefind as a post-build indexing step
`build` becomes `astro build && pagefind --site dist`. Pagefind reads the generated `dist/`
HTML and writes a static `/pagefind/` bundle into it. Alternative — an Astro integration
(`astro-pagefind`) — was considered; the plain CLI step is simpler, transparent, and has no
Astro-version coupling. Trade-off: the index only exists after a full build, so search is not
exercisable under `astro dev` — it must be tested against `astro build` + a static preview
(the same build-time constraint already true of our DB-backed pages).

### Custom UI via the Pagefind JS API, not the default Pagefind UI
Load the generated `/pagefind/pagefind.js` at runtime and render results with our own markup.
This gives full control to match the neon theme and to show the **content-type tag**
(Blog/Podcast), which the stock Pagefind UI does not surface. Alternative — mounting the
default `PagefindUI` component and overriding its CSS — was rejected: theming its internals is
brittle and it can't cleanly render our custom type tag. Cost: we own the results markup,
debounce, and empty/error states (all small).

### Marking indexable content
Add `data-pagefind-body` to the `<article>` in `PostArticle.astro` and
`EpisodeArticle.astro`. Once any page declares `data-pagefind-body`, Pagefind indexes **only**
tagged regions site-wide — so listing pages (`/blog`, `/podcast`) and all chrome are excluded
automatically, with no per-page ignore markers. The content-type tag is emitted via
`data-pagefind-meta` (e.g. `type:blog` / `type:podcast`) on the article; the page `<h1>` and a
leading paragraph give Pagefind the title and excerpt for result cards.

### Multilingual via `<html lang>` (already present)
Pagefind segments the index by the page's `<html lang>` and, when its library loads on a page,
serves results from that language's index. Because `Base.astro` already sets `pt-BR` / `en`,
per-language isolation is automatic — no extra configuration. Localized search strings
(placeholder, no-results, open/close/aria labels) are added to `STRINGS` in `i18n.js`.

### Loading the bundle without Vite interference
The `/pagefind/` bundle does not exist at Astro build time (it is produced right after), so it
must not be resolved by Vite. Load it with a dynamic `import(/* @vite-ignore */ "/pagefind/pagefind.js")`
at runtime, only when the modal is first opened (keeps it off the critical path). The bundle is
same-origin, so the site's strict CSP is unaffected.

### Modal lives in Base.astro
A single search trigger + modal in `Base.astro` makes search available on every page with one
implementation. The modal is a focus-trapped dialog opened by the header control or Ctrl/Cmd-K,
closed by Escape/backdrop, mirroring akita's "Buscar" nav entry.

## Risks / Trade-offs

- Search only works on a fully built site → mitigate by documenting `astro build && pagefind`
  + preview for local testing; wire Pagefind into the same build the VPS/Docker deploy runs.
- Deploy step must install `pagefind` and run it after the Astro build → add to
  `package.json` build script so any CI/Docker build produces `/pagefind/` automatically; a
  missing step would ship a site whose search 404s its index. The modal must degrade
  gracefully (show a localized error) if the bundle fails to load.
- Index freshness → the index is rebuilt every deploy from current published content, so it
  tracks the DB-backed pages exactly; no separate reindex job.
- Excerpt quality depends on content structure → `data-pagefind-body` on `<article>` plus the
  existing `<h1>`/first paragraph yields reasonable titles/excerpts; revisit
  `data-pagefind-meta` if cards look thin.
- Bundle size / requests → Pagefind lazy-loads per-language index shards on demand; loading the
  library only on first modal open avoids penalizing readers who never search.

## Open Questions

- Keyboard shortcut: Ctrl/Cmd-K (developer-audience convention) vs `/` (akita/GitHub style)?
  Default: Ctrl/Cmd-K, with `/` as a possible secondary binding.
- Should the podcast result tag deep-link to the episode page or offer an inline play action?
  Default: link to the episode page (consistent with blog results); inline play is a later
  enhancement.
