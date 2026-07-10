## Why

The dashboard's `/manage` page renders every blog post and podcast episode (any
status, both languages) as two flat tables ordered by language then date. As the
automated pipeline keeps producing content this piles up: today it is ~32 posts
and ~32 episodes, and because every topic exists in **both** PT and EN, half the
rows are the same content in the other language. Published and still-in-progress
items are interleaved, so finding what actually needs action means scanning the
whole list. The view has become hard to work with.

## What Changes

- Separate **unpublished (needs-action)** items from **published** items in each
  table. Needs-action is shown first; published is moved into a **collapsed,
  counted** section so it stays reachable but out of the way.
- Add lightweight **client-side filters** at the top of the page: a **language
  toggle** (All / PT / EN) and a **title search** box that hide non-matching rows
  live, with no page reload. Typing a query auto-expands the published section so
  matches there are visible.
- No change to the underlying data, routes, or the per-item actions (edit,
  publish/unpublish, upload audio, delete) — this is a presentation-only
  reorganization of the existing `MANAGE` template.

## Impact

- `pipeline/src/boosternews/dashboard/templates.py` — restructure the `MANAGE`
  template (row macros, needs-action vs. collapsed published, filter bar + inline
  filter script, styles).
- No route, repository, or schema changes; `list_all_posts()` / `list_all_episodes()`
  already return every item with its status and language.
- Capability `content-management`: the "Content management view" requirement is
  refined and a new "Management view organization and filtering" requirement is added.
