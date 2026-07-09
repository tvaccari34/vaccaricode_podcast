## 1. Build integration

- [ ] 1.1 Add `pagefind` as a devDependency in `web/package.json`.
- [ ] 1.2 Update the `build` script to `astro build && pagefind --site dist` so the `/pagefind/` bundle is generated into the static output.
- [ ] 1.3 Confirm the Docker/VPS deploy build runs the updated script (installs `pagefind` and produces `/pagefind/`); note it in deploy config/docs if a separate build step exists.

## 2. Make content indexable

- [ ] 2.1 Add `data-pagefind-body` to the `<article>` in `web/src/components/PostArticle.astro`, and `data-pagefind-meta="type:blog"` for the content-type tag.
- [ ] 2.2 Add `data-pagefind-body` to the `<article>` in `web/src/components/EpisodeArticle.astro`, and `data-pagefind-meta="type:podcast"`.
- [ ] 2.3 Verify listing/index pages and chrome (header/nav/footer) are excluded — i.e. no stray `data-pagefind-body` outside article content.

## 3. Localization

- [ ] 3.1 Add search UI strings to `web/src/lib/i18n.js` for PT and EN: trigger label ("Buscar"/"Search"), input placeholder, no-results message, and open/close/aria labels.

## 4. Search UI (modal + results)

- [ ] 4.1 Add a header search trigger in `web/src/layouts/Base.astro` (mirroring the nav pattern), labelled from i18n.
- [ ] 4.2 Add a focus-trapped search modal (dialog) in `Base.astro`, opened by the trigger and by Ctrl/Cmd-K, closed by Escape/backdrop.
- [ ] 4.3 On first open, dynamically load the bundle via `import(/* @vite-ignore */ "/pagefind/pagefind.js")`; degrade to a localized error if it fails.
- [ ] 4.4 Wire the input (debounced) to Pagefind search and render results with our own markup: title, matching excerpt, and a Blog/Podcast type tag from `data-pagefind-meta`; each result links to its page.
- [ ] 4.5 Rely on the page's `<html lang>` for per-language results (no cross-language leakage); confirm the PT and EN modals use their own localized strings.

## 5. Styling

- [ ] 5.1 Style the trigger, modal, input, result cards, type tag, and empty state in `web/src/styles/global.css` to match the neon theme (light + dark), with responsive behavior.

## 6. Verification

- [ ] 6.1 Run `astro build && pagefind --site dist` and preview the static output; confirm the `/pagefind/` bundle is generated.
- [ ] 6.2 On the PT site: open search (click + Ctrl/Cmd-K), query a known post and a known episode, confirm results show title/excerpt/type tag and navigate correctly; confirm only PT results appear.
- [ ] 6.3 On the EN site (`/en`): repeat and confirm only EN results and EN UI strings.
- [ ] 6.4 Confirm a no-match query shows the localized empty state, Escape/backdrop closes the modal, and listing/chrome pages are absent from results.
- [ ] 6.5 Check light/dark theme and narrow-viewport rendering of the modal and results.
