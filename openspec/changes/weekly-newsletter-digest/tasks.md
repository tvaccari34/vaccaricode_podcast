# Tasks — weekly newsletter digest

## 1. Database
- [x] 1.1 Migration `0006_newsletter_digests.sql`: table (id, language, campaign_id, item_count, window_start, window_end, created_at).

## 2. Stop per-post campaigns (publishing)
- [x] 2.1 Remove the `create_campaign` loop from `publish_topic`; still publish the newsletter draft + record a `newsletter` publication (no `external_id`).

## 3. Repository helpers
- [x] 3.1 `last_digest_end(language) -> datetime | None`.
- [x] 3.2 `posts_for_digest(language, since) -> list[dict]` — blog posts published since `since` (bounded 7d by caller), each with topic_id, title, blurb (newsletter draft body), public URL, published_at.
- [x] 3.3 `record_digest(language, campaign_id, item_count, window_start, window_end)`.

## 4. Digest module + Listmonk
- [x] 4.1 `listmonk.start_campaign(campaign_id)` (PUT status=running) for the auto-send path.
- [x] 4.2 `digest.build_digest_body(items, language) -> (subject, body)` — pure: localized intro + one section per post + footer.
- [x] 4.3 `digest.run_digest()` — per language compute window, gather items, skip if empty, create campaign, optional auto-send, record digest. Returns a summary.

## 5. Config + CLI
- [x] 5.1 Config: `newsletter_digest_subject` / `_en`, `newsletter_digest_intro` / `_en`, `newsletter_digest_autosend` (default false).
- [x] 5.2 CLI `boosternews digest` → `digest.run_digest()`; print the summary.

## 6. Schedule
- [x] 6.1 Weekly cron running `boosternews digest` as an ephemeral Swarm job (via `swarm-run.sh`).

## 7. Verify end-to-end
- [x] 7.1 Publishing a post creates **no** Listmonk campaign.
- [x] 7.2 `digest` with posts in the window creates **one** campaign per language aggregating them; records a digest row.
- [x] 7.3 Running `digest` again immediately creates nothing (window consumed).
- [x] 7.4 Empty window → no campaign, no digest row.
- [x] 7.5 (If autosend on) the campaign is started/sent.

## 8. Docs
- [x] 8.1 Update `deploy/NEWSLETTER.md` / README: weekly digest behavior, the cron, and the auto-send opt-in.
