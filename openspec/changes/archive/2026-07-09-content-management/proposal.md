## Why

Once content is published, the dashboard offers no way to see or manage it. The review queue only
lists **pending** drafts, and the "Episodes" section only lists pt-BR episodes for re-narration.
There is no place to see everything that exists — published or not — and no controls to take a
published post/episode back down, edit it, regenerate its audio, or delete it.

The owner needs a **content management view**: lists of all **blog posts** and **podcast
episodes**, in **Portuguese and English**, each with lifecycle actions — **publish, unpublish,
edit, regenerate audio, and delete**. This applies equally to automated and manually authored
content.

## What Changes

- **Dashboard "Manage" view**: two lists — Posts and Episodes — grouped by language, each row
  showing the item's status and its available actions.
- **Per-item lifecycle actions**:
  - **Publish** a specific post/episode (an explicit human action, independent of the automated
    approval gate).
  - **Unpublish** a published post/episode so it drops off the site/feed (kept in the DB, editable).
  - **Edit** a post (title + Markdown body) or an episode (title, script, show notes).
  - **Regenerate audio** for an episode — re-narrate (pt-BR worker) or upload a new MP3.
  - **Delete** a post/episode, removing it from the site and cleaning up its stored audio.
- **Repository helpers** to list all posts/episodes (any status, both languages) and to
  publish / unpublish / delete individual items.
- **Object storage**: delete an episode's audio object(s) when the episode is deleted.
- **On-demand rebuild**: management changes (and a **"Rebuild now"** button) queue a rebuild in a
  new `site_build_requests` table; a 1-minute host watcher consumes it and rebuilds the static site,
  so changes appear live within ~1 minute (the 5-minute cron remains as a safety net).

## Capabilities

### New Capabilities
- `content-management`: a dashboard view over **all** posts and episodes (pt-BR + English) with
  per-item publish / unpublish / edit / regenerate-audio / delete.

### Modified Capabilities
- `review-workflow`: the dashboard gains a management view (and post editing) alongside the
  pending-review queue.
- `publishing`: adds per-item **publish** and a new **unpublish** and **delete** lifecycle, beyond
  the existing topic-wide publish of approved drafts.
- `podcast-production`: deleting an episode removes its stored audio object(s).

## Impact

- **Dashboard**: a new `/manage` list view plus per-item action routes and a post edit form.
- **Repository**: `list_all_posts`, `list_all_episodes`, `publish_item`, `unpublish_draft`,
  `unpublish_episode`, `delete_draft`, `delete_episode` (episode delete cleans up audio + jobs).
- **Storage**: a new `delete_object(key)` helper (episode audio at `podcast/{id}.mp3` and
  `narration/{id}/raw.wav`).
- **Website**: no query changes — it already renders only `published` content, so unpublish/delete
  take effect on the next rebuild.
- **Operational**: destructive delete is confirmed in the UI; the site reflects changes within one
  cron rebuild cycle (≤5 min) unless a manual rebuild trigger is added.
