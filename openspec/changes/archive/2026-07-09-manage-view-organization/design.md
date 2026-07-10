## Context

`/manage` is served by the FastAPI review dashboard (`dashboard/app.py`) which
renders the `MANAGE` Jinja template (a string in `dashboard/templates.py`). The
route passes `posts=repo.list_all_posts()` and `episodes=repo.list_all_episodes()`
— every item, any status, both languages, ordered `language, updated_at DESC`.
Statuses seen today: posts `pending_review` / `published`; episodes `script_ready`
/ `ready` / `published` (plus `needs_edit` / `rejected` / `approved` defined in CSS).
The dashboard has no build step and no JS framework; the existing theme handling is
a small inline `<script>`. Styling is a single inline `<style>` block.

## Goals / Non-Goals

**Goals**
- Surface the actionable (unpublished) items first; keep published reachable but
  collapsed.
- Let the owner narrow the list by language and by title, instantly, client-side.
- Keep every existing per-item action and confirmation exactly as-is.

**Non-Goals**
- No route/repository/SQL changes, no pagination, no server-side filtering.
- No change to the review-queue (`/`) page or to the publish/edit/delete flows.
- Not merging the PT and EN rows of a topic into one (language stays a filter, not
  a grouping) — simpler and keeps per-language actions independent.

## Decisions

### Split by publish state in the template, not the query
Both lists already arrive in full. Partition them in Jinja
(`selectattr('status','equalto','published')` / `rejectattr(...)`) rather than
adding new repository methods — zero data-layer change, and "published" stays a
pure presentation bucket. Published rows go inside a `<details>` collapsed by
default with a count in the `<summary>`.

### Client-side filtering over data attributes
Each row carries `data-lang` and `data-title` (lowercased). A tiny inline script
toggles `tr.style.display` from a language toggle and a search input — consistent
with the dashboard's existing inline-script approach, no dependencies. Searching
sets `details.open = true` on the published sections so matches there surface.

### Row markup via Jinja macros
Extract `post_row(p)` / `episode_row(e)` macros so the needs-action and published
tables share one definition and can't drift; the publish-vs-unpublish button
already branches on `status` inside the row.

## Risks / Trade-offs

- Static section counts (`Needs action (N)`, `Published (M)`) reflect totals, not
  the filtered subset. Acceptable — the labels show the true totals; live per-filter
  counts would add JS for little value.
- A collapsed published section hides its rows until expanded; mitigated by
  auto-opening it whenever a title query is active.
- Language codes are compared exactly (`pt-BR`, `en`); the toggle buttons carry
  those exact values.
