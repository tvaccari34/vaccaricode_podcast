## 1. Restructure the MANAGE template

- [x] 1.1 Add Jinja macros `post_row(p)` and `episode_row(e)` holding the existing row markup (incl. the publish/unpublish branch and confirmations), and give each `<tr>` `data-lang` + lowercased `data-title` attributes.
- [x] 1.2 Partition posts/episodes in-template into needs-action (`rejectattr status == published`) and published (`selectattr status == published`); render needs-action first, published inside a collapsed `<details>` with a counted `<summary>`.
- [x] 1.3 Keep the total counts on the `Posts` / `Episodes` headings and add per-group counts.

## 2. Filters

- [x] 2.1 Add a filter bar: language toggle (All / PT=`pt-BR` / EN=`en`) and a title `search` input.
- [x] 2.2 Add an inline script that hides non-matching `tr[data-lang]` rows by language + title substring, and sets `details.open` when a title query is active.
- [x] 2.3 Add styles for the filter bar, active toggle state, and the collapsed published section.

## 3. Verification

- [x] 3.1 Render the template with representative data and confirm valid HTML: needs-action tables first, published collapsed, every item present, actions unchanged.
- [x] 3.2 Rebuild the pipeline image and load `/manage` on the live dashboard: confirm the separation, language toggle, and title search all work and all items remain reachable.
