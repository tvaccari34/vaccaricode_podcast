# Design — weekly newsletter digest

## Context

`publish_topic` currently loops over approved drafts and, for each `newsletter` draft, calls
`listmonk.create_campaign(...)` — one campaign per post per language. Listmonk campaigns are created
as **drafts** (not sent) via `POST /api/campaigns`; `list_id_for(language)` maps a language to its
list. Publications are recorded in the `publications` table (channel, ref_id, language,
published_at). Each post has a `newsletter` draft (an AI-written blurb) and a `blog` draft, per
language.

## Goals

- One **weekly** newsletter campaign per language, aggregating the last 7 days of posts.
- No per-post emails.
- Idempotent: no post included twice; empty weeks produce no campaign.

## Non-Goals

- Auto-sending by default (kept opt-in), changing list/segment logic, HTML template design, or an
  AI-written weekly intro (a deterministic template is enough for v1; AI intro can come later).
- Podcast-episode-only digests (episodes ride along with their post; the digest is post-driven).

## Decisions

### 1. Digest items = blog posts published in the window, using the newsletter blurb
For each language, select **blog** publications (from `publications`, `channel='blog'`) in the
window, and for each, pull the post's **`newsletter` draft body** (the blurb) + blog **title** +
the public **blog URL**. This reuses the content the pipeline already writes and gives a clean
"section per post".

### 2. Window = since the last digest (bounded to 7 days)
`window_start = max(last digest window_end for this language, now - 7 days)`; `window_end = now`.
- Using the last digest's end makes it idempotent (running twice back-to-back finds nothing new).
- Bounding to 7 days avoids a huge first digest if none was ever sent.

### 3. Track digests in a new table
`newsletter_digests(id, language, campaign_id, item_count, window_start, window_end, created_at)`.
`last_digest_end(language)` = `max(window_end)`. Recording a row both marks the window consumed and
gives an audit trail.

### 4. One campaign per language, created as a draft (opt-in auto-send)
Compose a Markdown body: a localized intro ("This week in software & AI…") + one `##` section per
post (title, blurb, "Read more" link) + a footer. Create it with `create_campaign` (draft). If
`NEWSLETTER_DIGEST_AUTOSEND` is true, also start it (`PUT /api/campaigns/{id}/status`
→ `running`). Default **off** — the owner reviews and sends, consistent with the approval gate.

### 5. Empty week → skip
If no posts in the window for a language, create no campaign and record no digest (so the window
stays open until there's content).

### 6. Scheduling: a weekly cron running a one-off Swarm job
`boosternews digest` runs weekly (e.g. Mondays) via a host cron using `swarm-run.sh` (same pattern
as publish/rebuild). Not the minute-interval scheduler (a weekly cadence there is awkward, and a
cron is explicit/inspectable).

### 7. Publishing stops creating campaigns
Remove the `create_campaign` loop from `publish_topic`. The `newsletter` draft is still published
and a `newsletter` publication is still recorded (no `external_id`), so the corpus/audit is intact;
it just doesn't email on its own.

## Data / API surface

- Migration `0006_newsletter_digests`.
- `repository.posts_for_digest(language, since) -> [{topic_id, title, blurb, url, published_at}]`.
- `repository.last_digest_end(language) -> datetime | None`; `record_digest(language, campaign_id, item_count, window_start, window_end)`.
- `digest.build_digest_body(items, language) -> (subject, markdown_body)` (pure, testable).
- `digest.run_digest()` → per language: gather, compose, `create_campaign`, optional auto-send, record.
- `listmonk.start_campaign(campaign_id)` (auto-send path).
- CLI: `boosternews digest`.

## Risks / trade-offs

- **Timing vs. publish cadence**: posts published *after* the weekly run wait for next week — fine
  for a weekly digest; the "since last digest" window guarantees none are dropped.
- **Auto-send is powerful**: default off; when on, the digest emails subscribers unattended — the
  owner opts in explicitly.
- **List config required**: if Listmonk isn't configured, `create_campaign` no-ops (as today) and
  the digest records nothing, so it stays a no-op until lists/token are set.

## Alternatives considered

- **Per-post campaign, digest as a Listmonk "template"** — rejected: doesn't aggregate; still one
  email per post.
- **Scheduler job with a 7-day interval** — rejected: the minute-based scheduler is a poor fit for
  weekly cadence and harder to reason about than an explicit cron.
