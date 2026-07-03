# Tasks — manual content authoring

## 1. Database
- [x] 1.1 Add migration `000X_topic_origin.sql`: `ALTER TABLE topics ADD COLUMN origin text NOT NULL DEFAULT 'auto';` (optional CHECK `origin IN ('auto','manual')`).
- [x] 1.2 Run `boosternews.migrate`; confirm existing rows default to `origin='auto'`.

## 2. Pipeline coexistence guardrails (content-generation)
- [x] 2.1 Add `origin='auto'` filter to the generate topic-selection query (`next_topic_for_generation` / repository) so `manual` topics are never generated.
- [x] 2.2 Add the same guard to topic **scoring** and any extract selection.
- [x] 2.3 Test: a `manual` topic with a hand-written draft is left untouched by `ingest`/`extract`/`generate`/scoring.

## 3. Repository helpers (manual-authoring)
- [x] 3.1 `create_manual_topic(title) -> topic_id` (origin='manual', status='selected', score=0).
- [x] 3.2 `upsert_manual_draft(topic_id, language, channel, title, body, approve=False)` → draft in `pending_review` (or `approved`).
- [x] 3.3 `create_manual_episode(topic_id, language, title, script, show_notes)` → episode (`script_ready`) + `podcast` draft.
- [x] 3.4 Reuse `enqueue_narration` / audio-upload / `episode_audio_target_status` for episode audio.

## 4. Dashboard — Create Post (review-workflow)
- [x] 4.1 `GET /create/post` form: language checkboxes (pt-BR/English), per-language title + Markdown body + optional newsletter blurb.
- [x] 4.2 `POST /create/post`: create synthetic topic + blog (and optional newsletter) drafts per chosen language; support "Save as draft" vs "Save & approve".
- [x] 4.3 Link "Create Post" from the dashboard header; validate at least one language + non-empty title/body.

## 5. Dashboard — Create Episode (review-workflow + podcast-production)
- [x] 5.1 `GET /create/episode` form: language checkboxes, per-language title + script + show notes; audio choice (pt-BR: enqueue narration; English: upload later).
- [x] 5.2 `POST /create/episode`: create synthetic topic (reuse if paired with a post) + episode + podcast draft per language; optionally enqueue pt-BR narration.
- [x] 5.3 Ensure the new episode shows in the existing "Episodes — edit script & re-narrate" and English-audio-upload sections.

## 6. Verify end-to-end
- [x] 6.1 Manual post (pt-BR + English) → appears in review queue → approve → publish → live on `/blog` + `/en/blog` + RSS.
- [x] 6.2 Manual episode pt-BR → enqueue narration → worker produces audio → publish → in `/podcast/feed.xml` with enclosure.
- [x] 6.3 Manual episode English → upload MP3 → publish → on `/en/podcast/`.
- [x] 6.4 Regression: automated pipeline still discovers/generates/publishes; manual topics remain untouched.

## 7. Docs
- [x] 7.1 Note manual authoring in `deploy/DEPLOY.md` / README (how to create a post/episode, the self-approve option, that manual content coexists with automation).
