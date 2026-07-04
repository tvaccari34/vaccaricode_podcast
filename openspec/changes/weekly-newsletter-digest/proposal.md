## Why

Today, publishing a post immediately turns its approved newsletter draft into a **Listmonk
campaign** — one campaign **per post, per language** (`publish_topic` in `publish.py`). That means
subscribers would get a separate email every time a post goes out, which is noisy and isn't how a
weekly newsletter should work.

The newsletter should instead be a **weekly digest**: aggregate the posts published in the **last 7
days** into a **single campaign per language** that summarizes the week, with one section per post
(title + blurb + link).

## What Changes

- **Publishing no longer creates a per-post campaign.** A published post still records its blog /
  podcast / newsletter publications; it just doesn't email anyone by itself.
- **A weekly digest job** collects the posts published since the last digest (bounded to ~7 days),
  per language, composes one newsletter body (a "this week" intro + a section per post with its
  blurb and a link), and creates **one Listmonk campaign per language**.
- **Digests are tracked** so a post is never included twice, and a week with **no new posts sends
  nothing**.
- **Created as a draft by default** for a human to review and send (matching the platform's
  human-in-the-loop ethos), with an optional **auto-send** setting for full automation.
- **Runs weekly** via a cron entry (`boosternews digest`), consistent with the existing operational
  crons.

## Capabilities

### New Capabilities
- `newsletter-digest`: weekly aggregation of the last 7 days of posts into a single Listmonk
  campaign per language, summarizing the week.

### Modified Capabilities
- `publishing`: no longer creates a Listmonk campaign when an individual post is published — the
  weekly digest owns campaign creation.

## Impact

- **Database**: migration `0006_newsletter_digests` (tracks each digest: language, campaign id,
  window, item count).
- **Pipeline**: new `boosternews.digest` module + `digest` CLI command; repository queries for the
  week's posts and to record digests. `publish.py` drops the per-post `create_campaign` call.
- **Config**: digest subject/intro strings per language and an optional `NEWSLETTER_DIGEST_AUTOSEND`
  flag (default off).
- **Ops**: a weekly cron runs the digest as an ephemeral Swarm job (like `publish`/`rebuild`).
- **Behavior change**: subscribers get one weekly email instead of one per post.
