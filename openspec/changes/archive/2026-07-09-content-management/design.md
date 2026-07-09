# Design — content management

## Context

Content is modelled as `topics → drafts (per channel, per language) → episodes (per language)`.
The site build reads only `status = 'published'` rows (`getPublishedPosts`, `getPublishedEpisodes`).
The dashboard today surfaces only pending drafts (review queue) and pt-BR episodes (re-narrate).
Publishing exists (`publish_all` / `publish_draft` / `publish_episode`) but is topic-wide and gated
to `approved` drafts; there is **no unpublish, no delete, and no all-content list**.

A **blog post** = a `drafts` row (`channel='blog'`, one per language). An **episode** = an
`episodes` row (one per language) with a paired `podcast` draft. Both automated and manually
authored content use these same rows.

## Goals

- One dashboard view listing **all** blog posts and episodes, pt-BR + English, with their status.
- Per-item **publish, unpublish, edit, regenerate audio, delete**.
- Works for automated and manual content alike; the site reflects changes after a rebuild.

## Non-Goals

- Newsletter management (same pattern could extend later).
- Version history / drafts-of-drafts, scheduling, or bulk operations.
- Changing the site theme, URLs, or feeds.

## Decisions

### 1. Management "publish" is an explicit human action (bypasses the automated gate)
`publish_draft` currently raises unless the draft is `approved` (that gate protects the *automated*
pipeline). From the management view the human is deciding directly, so add a `publish_item` that
sets the draft (and, for podcast, its episode) to `published` and records a publication regardless
of prior status. The automated pipeline keeps its gate unchanged.

### 2. Unpublish flips status away from `published`
- Blog/newsletter draft: `published → approved` (stays available and editable, just off the site).
- Episode: `published → ready` (keeps its audio; just off the feed/site).
Because the site selects `status='published'`, the item disappears on the next rebuild.

### 3. Edit is in place
- **Post**: an edit form updates the draft `title`/`body`; status is preserved (editing a published
  post keeps it published, so the rebuild shows the new text).
- **Episode**: reuse the existing "edit script & re-narrate" (script) and audio upload; the manage
  row links to them. Title/show-notes edits update the episode in place.

### 4. Delete targets the specific row, not the topic
- **Post**: delete the `drafts` row (`channel='blog'`, that language). Leave the topic and any
  sibling content (other language, episode, newsletter) intact.
- **Episode**: delete the `episodes` row (cascades to `narration_jobs`), delete its paired `podcast`
  draft, and delete the stored audio object(s) via `storage.delete_object` — `podcast/{id}.mp3` and
  `narration/{id}/raw.wav`.
- Optionally prune a topic once it has no drafts/episodes left (open question; low priority).

### 5. On-demand rebuild via a request queue + host watcher
Management mutations are DB-only, so the site must be rebuilt to reflect them. The dashboard
container can't run the Node build directly, so instead every mutation (and an explicit "Rebuild
now" button) inserts a row into `site_build_requests`. A **1-minute host cron watcher**
(`deploy/rebuild-watch.sh`) consumes pending rows and runs `publish-rebuild.sh rebuild`, so changes
appear on the live site within ~1 minute. The existing 5-minute cron stays as a safety net (it also
catches scheduler-published content, which doesn't set the flag). The `narration /complete` handler
and the audio-upload route also queue a rebuild so regenerated audio appears promptly.

### 6. Destructive actions are confirmed
Delete (and unpublish) use a confirm step in the UI (JS `confirm` or a confirm page) so a stray
click can't drop live content.

## Data / API surface

Storage: `delete_object(key)` (ignore "not found").

Repository:
- `list_all_posts()` → blog drafts across languages: `{id, topic_id, language, title, status, updated_at, origin}`.
- `list_all_episodes()` → episodes across languages: `{id, language, title, status, audio_url, duration, origin}`.
- `publish_item(draft_id)` / `publish_episode_item(episode_id)` — set `published`, record publication.
- `unpublish_draft(draft_id)`, `unpublish_episode(episode_id)`.
- `delete_draft(draft_id)`, `delete_episode(episode_id)` (returns audio keys to purge).

Dashboard routes (all behind the existing Basic Auth):
- `GET /manage` — the list view.
- `POST /manage/post/{draft_id}/{publish|unpublish|delete}`; `GET/POST /manage/post/{draft_id}/edit`.
- `POST /manage/episode/{id}/{publish|unpublish|delete}`; reuse `/episode/{id}/renarrate` and
  `/episode/{id}/audio` for audio.

## Risks / trade-offs

- **Rebuild delay**: unpublish/delete aren't visible on the site until the next rebuild (≤5 min).
  Mitigate with a clear UI note; a manual trigger removes it (follow-up).
- **Bypassing the approval gate** in `publish_item` is intentional and scoped to the manual
  management action; the automated pipeline's gate is untouched.
- **Delete is destructive**: guarded by confirmation and by targeting a single row (no topic-wide
  cascade), with explicit audio cleanup.

## Alternatives considered

- **Reuse the review queue for management** — rejected: the queue is keyed to pending drafts and
  can't show/act on published content.
- **Trigger a rebuild synchronously from the dashboard** — deferred: heavy (Node build) and not
  cleanly runnable from the dashboard container; the cron already keeps the site in sync.
