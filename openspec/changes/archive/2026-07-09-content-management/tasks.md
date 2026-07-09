# Tasks — content management

## 1. Object storage
- [x] 1.1 `storage.delete_object(key)` — delete one object; ignore "not found".

## 2. Repository helpers
- [x] 2.1 `list_all_posts()` → all blog drafts (any status), both languages: id, topic_id, language, title, status, updated_at, origin.
- [x] 2.2 `list_all_episodes()` → all episodes (any status), both languages: id, language, title, status, audio_url, duration, origin.
- [x] 2.3 `publish_item(draft_id)` and `publish_episode_item(episode_id)` → set `published` + `record_publication` (explicit human publish; no approval-gate error).
- [x] 2.4 `unpublish_draft(draft_id)` (`published→approved`) and `unpublish_episode(episode_id)` (`published→ready`).
- [x] 2.5 `delete_draft(draft_id)`; `delete_episode(episode_id)` — delete row (+ paired podcast draft, cascade narration_jobs) and return audio keys to purge.

## 3. Dashboard — management view (content-management + review-workflow)
- [x] 3.1 `GET /manage`: Posts list + Episodes list, grouped by language, showing status + per-item actions; link it from the dashboard header.
- [x] 3.2 Post actions: `POST /manage/post/{id}/publish`, `/unpublish`, `/delete` (delete + unpublish confirmed in UI).
- [x] 3.3 Post edit: `GET /manage/post/{id}/edit` (title + Markdown body prefilled) + `POST` to save in place.
- [x] 3.4 Episode actions: `POST /manage/episode/{id}/publish`, `/unpublish`, `/delete` (delete purges audio via `storage.delete_object`).
- [x] 3.5 Episode audio: link each episode row to the existing `/episode/{id}/renarrate` (re-narrate) and `/episode/{id}/audio` (upload).

## 4. Site sync
- [x] 4.1 Confirm unpublish/delete/edit are reflected by the existing 5-minute cron rebuild; show a UI note about the delay.
- [x] 4.2 Manual "Rebuild now" button + DB request queue (`site_build_requests`, migration 0005) consumed by a 1-minute host watcher (`deploy/rebuild-watch.sh`); management mutations auto-queue a rebuild too.

## 5. Verify end-to-end
- [x] 5.1 Publish then unpublish a pt-BR and an English **post**; confirm it appears/disappears from `/blog` (+ `/en/blog`) + RSS after rebuild.
- [x] 5.2 Publish/unpublish a pt-BR and English **episode**; confirm feed/index reflect it after rebuild.
- [x] 5.3 Edit a post body; confirm the live text updates after rebuild.
- [x] 5.4 Regenerate episode audio (re-narrate pt-BR; upload English) from the manage view.
- [x] 5.5 Delete a post and an episode; confirm removal from the site and that episode audio object(s) are purged from storage.
- [x] 5.6 Regression: automated + manual content both appear in the lists and the pipeline is unaffected.

## 6. Docs
- [x] 6.1 Document the manage view + actions and the rebuild-delay note in README / `deploy/DEPLOY.md`.
