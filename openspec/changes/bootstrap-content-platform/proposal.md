## Why

Tiago Vaccari wants a personal media presence at **tiagovaccari.com** covering trends in
the IT / software-development space — but producing a blog, a newsletter, and a podcast by
hand is unsustainable for one person. The goal is an **automated content factory**: it
discovers what's trending in software/AI, then turns a single news item into a blog post, a
newsletter section, and a narrated podcast episode from the same source material. This
mirrors the cadence and topic mix of akitaonrails.com while keeping a human in control of
quality. No platform exists yet — this change bootstraps it from an empty repository.

## What Changes

- **Trend discovery**: scheduled ingestion of IT/dev trends from RSS feeds, aggregators
  (Hacker News, Lobsters, GitHub Trending, dev.go newsletters), and APIs; dedup, score, and
  store candidate topics.
- **AI content generation**: from one approved topic, generate a blog post (markdown),
  a podcast script, and a newsletter blurb using Google Gemini Flash, grounded in the extracted
  source articles.
- **Podcast narration + sound server**: a self-hosted FastAPI **sound server** synthesizes
  narration from the script with an open neural TTS model (voice cloning supported), then
  assembles a normalized, chaptered MP3 with intro/outro via ffmpeg.
- **Human review queue**: an approval dashboard where drafts (blog + newsletter + audio
  preview) are reviewed and approved before anything publishes.
- **Website**: an Astro static site for blog + podcast (episodes + show notes), an
  **about/bio page** for Tiago, and a themed **newsletter subscribe page**; it generates an
  RSS feed and an iTunes-compatible podcast feed.
- **Newsletter**: self-hosted Listmonk for lists, double opt-in, themed subscribe page,
  campaigns, and analytics, sending through a transactional SMTP provider.
- **Infrastructure**: an always-on VPS runs all public/stateful services (Astro site,
  pipeline, PostgreSQL, S3-compatible object storage, Listmonk, review dashboard) via Docker
  Compose; the home computer runs only a GPU sound-worker that pulls narration jobs from the
  VPS and uploads audio back (outbound-only, no inbound exposure).

## Capabilities

### New Capabilities
- `trend-discovery`: scheduled multi-source ingestion, extraction, dedup, and scoring of
  trending IT/dev topics into a candidate queue.
- `content-generation`: Gemini-driven generation of blog post, podcast script, and
  newsletter blurb from one approved topic, grounded in source articles.
- `podcast-production`: the self-hosted sound server (TTS synthesis + voice + audio
  assembly) that turns a script into a publishable, chaptered podcast episode.
- `review-workflow`: human approval queue and dashboard gating all publishing, with
  per-channel approve/reject/edit.
- `publishing`: rendering and release of approved content to the blog, the podcast feed,
  and the newsletter, plus RSS/iTunes feed generation.
- `website`: the Astro public site — blog, podcast pages, about/bio, and the themed
  newsletter subscribe page.
- `newsletter-subscription`: Listmonk-backed subscribe flow with double opt-in,
  LGPD/GDPR-compliant data handling, and campaign delivery.
- `platform-infrastructure`: PostgreSQL, object storage, secrets, scheduling, and the
  Docker Compose deployment that ties the services together.

### Modified Capabilities
<!-- None — greenfield project, no existing specs. -->

## Impact

- **New repository layout**: `pipeline/` (Python), `sound-server/` (Python/FastAPI),
  `web/` (Astro), `sound-worker/` (home GPU), `deploy/` (VPS Compose + home worker Compose,
  Listmonk config), `db/` (migrations).
- **External dependencies**: Google Gemini API; trend sources (Hacker News/GitHub/RSS);
  a pluggable transactional SMTP provider (Amazon SES or Resend) for newsletter delivery; the
  XTTS-v2 model weights (downloaded to the home worker).
- **Infrastructure**: an always-on VPS (PostgreSQL, S3-compatible storage, services, TLS for
  tiagovaccari.com) plus the home computer's NVIDIA RTX 4060 Ti for the sound-worker. The two
  communicate over authenticated outbound HTTPS from home to the VPS.
- **Operational**: API keys + SMTP credentials as secrets; a human reviewer in the loop;
  podcast feed submission to Apple/Spotify directories (manual, one-time).
