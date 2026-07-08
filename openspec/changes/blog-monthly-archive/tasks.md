## 1. Localization groundwork

- [x] 1.1 Add ordered month-name arrays for PT and EN to `web/src/lib/i18n.js` (index 0–11).
- [x] 1.2 Add archive UI strings per locale to `i18n.js` (e.g. table-of-contents heading / "Archive" label).

## 2. Grouping logic

- [x] 2.1 Add a helper (used by `PostList.astro`) that takes the `updated_at`-sorted posts + `lang` and returns groups `[{ year, monthIndex, anchorId, label, posts }]`, preserving reverse-chronological order.
- [x] 2.2 Derive `anchorId` as lowercase `"{year}---{english-month-name}"` (e.g. `2026---july`) from year/month numbers; assert ids are unique across groups.
- [x] 2.3 Build `label` as "YYYY - MonthName" using the localized month-name array for the given `lang`.

## 3. Listing component rendering

- [x] 3.1 Update `web/src/components/PostList.astro` to render each group as a month heading with `id={anchorId}` followed by that group's posts, keeping the existing `.card` / `.meta` markup for each post.
- [x] 3.2 Add a TOC fragment/markup listing every group as an anchor link (`href="#{anchorId}"`, localized label), reusing the same group list so the TOC and headings can never drift.

## 4. Page layout + styles

- [x] 4.1 Wrap the list + TOC in a two-column layout in `web/src/pages/blog/index.astro` (PT), main list first in DOM order, TOC in an `<aside>`.
- [x] 4.2 Mirror the same layout in `web/src/pages/en/blog/index.astro` (EN), passing `lang="en"`.
- [x] 4.3 Add CSS to `web/src/styles/global.css`: two-column grid, sticky TOC (`position: sticky`, `top`, max-height/overflow), and a breakpoint that hides/stacks the sidebar so the single-column list stays fully usable.

## 5. Verification

- [x] 5.1 Run `astro build` and confirm both `/blog` and `/en/blog` render month headings with correct anchor ids and localized month names.
- [x] 5.2 Verify each TOC entry scrolls to its month section, and that the TOC lists only months that contain posts.
- [x] 5.3 Check responsive behavior: at narrow widths the sidebar collapses/hides and every post remains reachable in the main column; verify light/dark theme both look correct.
