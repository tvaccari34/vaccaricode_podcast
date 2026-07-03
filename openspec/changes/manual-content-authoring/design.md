# Design — manual content authoring

## Context

The pipeline models everything as `topics → drafts (per channel, per language) → episodes (per
language)`, gated by a review dashboard and released by `publish`. The website reads **published**
drafts/episodes from Postgres at build time. Manual authoring must plug into this model so that
hand-written content is indistinguishable downstream from generated content, while the automated
pipeline keeps running untouched.

Key existing constraints (from the schema):
- `drafts.topic_id` and `episodes.topic_id` are **NOT NULL** foreign keys → any content needs a
  `topics` row.
- `drafts` are unique per `(topic_id, channel, language)`; `episodes` unique per `(topic_id,
  language)`.
- The site/feed queries select `status = 'published'` (episodes additionally need `audio_url` for
  the feed enclosure). Review queue selects drafts in `pending_review` / `needs_edit`.
- Narration already works: `enqueue_narration()` + the home worker for pt-BR; the dashboard MP3
  upload route for English.

## Goals

- Author a **post** (blog + optional newsletter) and an **episode** (script + show notes) by hand,
  in pt-BR and/or English, from the dashboard.
- Manual content is first-class: same review, publish, site, RSS, and podcast feed.
- Automated and manual authoring **coexist**; the pipeline never re-processes manual content.

## Non-Goals

- Rich-text/WYSIWYG editing (plain Markdown textarea is enough; matches how drafts store `body`).
- Custom slugs/permalinks (reuse the existing `topic_id`-based URLs; slugs can be a later change).
- Scheduling/backdating publication; changing the site theme or feed structure.
- Bulk import.

## Decisions

### 1. Synthetic topic + `origin` flag (not a nullable `topic_id`)
Create a real `topics` row for each manual entry and add `topics.origin ∈ {auto, manual}`.
- **Why**: `drafts`/`episodes` require `topic_id`; a synthetic topic keeps every downstream query
  (review queue, publish, site render, feed) working with **zero changes**. Making `topic_id`
  nullable would ripple through many joins.
- The synthetic topic is created with `origin='manual'`, `status='selected'`, `score=0`,
  `title = <the post/episode title>`, and no `extracted_text`/`urls`.

### 2. The pipeline ignores `manual`-origin topics
Add `AND origin = 'auto'` (or `origin <> 'manual'`) to the automation's topic-selection points:
- topic **scoring** (don't score manual topics),
- `next_topic_for_generation` / the generate step (never generate over a manual topic),
- extract (already filtered by `status='new' AND extracted_text IS NULL`; manual topics are
  `selected` with no source URLs, so they're naturally excluded — add the explicit `origin` guard
  for safety).
Ingest is unaffected (it creates its own `auto` topics). Review and publish intentionally include
manual topics — that's how they flow to the site.

### 3. Reuse review → publish → render unchanged
Manual drafts are created in `pending_review`; manual episodes in `script_ready`. They appear in
the existing review queue and are released by the existing `publish` (which flips approved drafts
and their episodes to `published`). No website or publishing code changes.
- **Optional self-approve**: because the author is also the reviewer, the create forms offer a
  "Save & approve" action that records an `approve` review immediately (equivalent to creating +
  approving in one step). Default is "Save as draft" (→ `pending_review`).

### 4. Narration for manual episodes mirrors generated episodes
- **pt-BR**: on episode create (or via the existing "Episodes — edit script & re-narrate" section)
  the author can **enqueue auto-narration** → home GPU worker synthesizes and uploads the MP3.
- **English**: author records and **uploads the MP3** via the existing
  `POST /episode/{id}/audio` route.
Both reuse existing code (`enqueue_narration`, `episode_audio_target_status`, upload handler).

### 5. Bilingual is per-language and optional
The forms let the author fill pt-BR, English, or both. Each language is created independently
(its own draft/episode rows). Authoring only English is valid (no pt-BR requirement), unlike the
auto pipeline which always produces the primary language first.

## Data model

```
ALTER TABLE topics ADD COLUMN origin text NOT NULL DEFAULT 'auto';  -- 'auto' | 'manual'
-- optional: CHECK (origin IN ('auto','manual'))
```
No other DDL. Manual content = one synthetic `topics` row (`origin='manual'`) + the usual
`drafts` (blog/newsletter, per language) and/or `episodes` (+ podcast `drafts`) rows.

## Flows

**Create Post**
1. Author opens "Create Post", picks language(s), enters title + Markdown body (+ optional
   newsletter blurb) per language.
2. Server creates a synthetic manual topic (once), then a `blog` draft (and optional `newsletter`
   draft) per chosen language in `pending_review` (or `approved` if "Save & approve").
3. Appears in the review queue → approve → `publish` → live on the blog + RSS.

**Create Episode**
1. Author opens "Create Episode", picks language(s), enters title, script, show notes.
2. Server creates the synthetic topic (reused if the post already made one for this entry), an
   `episode` per language, and a `podcast` draft per language.
3. Audio: pt-BR → "enqueue narration" (worker) ; English → upload MP3. Feed includes the episode
   once it's `published` **and** has `audio_url`.

## Risks / trade-offs

- **Synthetic topics accumulate**: manual topics live in the `topics` table. Mitigated by the
  `origin` filter (excluded from automation) and being harmless to storage. A future cleanup/admin
  view is out of scope.
- **Uniqueness**: one synthetic topic per manual "entry" keeps `(topic_id, channel, language)` and
  `(topic_id, language)` uniqueness intact. Creating a post and an episode as one editorial unit
  should reuse the same topic; creating them separately makes separate topics — acceptable.
- **URL collisions**: reusing `topic_id` URLs avoids slug collisions entirely.

## Alternatives considered

- **Nullable `topic_id` + a separate `manual_posts` table** — rejected: duplicates the render/
  publish paths and forces site/feed changes.
- **Publish-directly (skip review)** — rejected as the default: keeps the human-in-the-loop gate
  consistent; offered instead as an explicit "Save & approve" shortcut.
