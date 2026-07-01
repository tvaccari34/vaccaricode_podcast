## Context

Greenfield project in an empty repository. The owner (Tiago Vaccari) is a solo
operator who wants the cadence and topic mix of akitaonrails.com (frequent posts on
AI/LLMs, languages, devops) plus a self-owned newsletter like themakitachronicles.com and a
narrated podcast — without doing the production by hand. The stack was decided with the user:
Python pipeline + Astro site + self-hosted Listmonk + a self-hosted TTS sound server, with a
human approval gate before anything publishes. Google Gemini Flash is the LLM. The podcast is
narrated in Tiago's own cloned voice. Topology: an always-on **VPS** hosts everything public
and stateful — the Astro site, the pipeline (trend search + processing), PostgreSQL, object
storage, Listmonk, and the review dashboard. The **only** thing that runs on Tiago's home
computer is voice generation: a GPU **sound-worker** (NVIDIA RTX 4060 Ti) that pulls narration
jobs from the VPS, synthesizes with XTTS-v2, and uploads the audio back — outbound HTTPS only,
nothing inbound exposed on the home network.

## Goals / Non-Goals

**Goals:**
- One discovered news item can fan out into a blog post, a podcast episode, and a newsletter
  section from the same source material.
- Self-hosted, self-owned data: subscribers (Listmonk), audio (object storage), and content
  (markdown in the repo).
- Human-in-the-loop: drafts are reviewed and approved before publishing.
- Reproducible deployment via Docker Compose; no per-minute TTS cost.
- Topic mix and date-based content layout inspired by the akitaonrails sites.

**Non-Goals:**
- Fully autonomous publishing (explicitly deferred; review queue first).
- Multi-tenant / multi-author CMS — single owner only.
- Mobile apps or a native podcast app — distribution is via standard RSS/Apple/Spotify.
- Real-time/live audio — episodes are batch-produced.
- Commercial TTS as the primary engine (kept only as a possible future fallback).

## Decisions

### Architecture (services)
Two locations: an always-on VPS (Docker Compose) and a home GPU sound-worker.

```
  VPS (always-on, public)                          HOME PC (RTX 4060 Ti)
  ┌──────────────────────────────────────────┐     ┌─────────────────────────┐
  │ pipeline (Python):                        │     │ sound-worker (Python):  │
  │  ingest → extract → score → generate      │◀─poll│  pull narration job →   │
  │  (Gemini) → enqueue narration job →       │     │  XTTS-v2 cloned voice → │
  │  assemble episode (ffmpeg) → publish      │─audio▶│  upload WAV back        │
  │                                           │ back │ (outbound HTTPS only,   │
  │ PostgreSQL · object storage (MinIO/S3)    │     │  no inbound exposure)   │
  │ review dashboard ──approve──▶ publishing  │     └─────────────────────────┘
  │ Astro site (blog/podcast/about/subscribe) │
  │ Listmonk ──▶ pluggable SMTP (SES | Resend)│
  │ podcast RSS/iTunes feed + episode pages   │
  └──────────────────────────────────────────┘
   served from the VPS (Caddy/nginx + TLS); audio from object storage

  Only voice generation runs at home. The home box opens NO inbound ports and
  needs NO static IP: it connects out to the VPS, claims pending narration
  jobs, and uploads results. If the home PC is asleep/offline, jobs simply
  queue on the VPS and drain when it returns — the public site is unaffected.
```

### Language & frameworks
- **Pipeline: Python.** Chosen because every hard part (article extraction via `trafilatura`,
  RSS via `feedparser`, the Gemini SDK, and especially open TTS models — Kokoro / XTTS-v2 /
  F5-TTS, all PyTorch) is Python-first. TypeScript/Ruby would shell out to Python for TTS
  anyway, so a single Python core is simpler for the part that matters most.
- **Site: Astro (astro.build).** Static output (cheap, fast, same hosting story as Akita's
  Hugo), content collections of markdown/MDX so the pipeline just writes a file, built-in
  RSS + podcast feed generation, and the ability to add the interactive subscribe form and a
  light/dark theme without a heavy framework.
- **Newsletter: Listmonk** (self-hosted, open source) for self-owned subscriber data, double
  opt-in, a themeable subscribe page, and campaigns — matching the self-built feel of
  themakitachronicles.com. Sending via a **pluggable SMTP provider**: Listmonk holds multiple
  named SMTP server configs, so delivery can switch between **Amazon SES and Resend** (both
  expose SMTP endpoints) by selecting a config — no code change.
- **Sound-worker: Python + XTTS-v2** on the home GPU (RTX 4060 Ti, ~4 GB VRAM needed — ample).
  XTTS-v2 is chosen over Kokoro/Piper specifically because it supports **voice cloning** from a
  short reference sample (zero-shot, no fine-tuning) and is multilingual (English + Portuguese),
  so the podcast narrates in **Tiago's own cloned voice**. It runs as a job-pulling worker, not
  a public server. (F5-TTS kept as an alternative clone model if XTTS quality lags.)

### Data model (initial, PostgreSQL)
- `sources` — configured feeds/APIs and their cadence.
- `topics` — deduped candidate trends (title, urls[], extracted_text, score, status).
- `drafts` — generated artifacts per topic per channel (blog/script/newsletter), with body
  and per-channel review status.
- `episodes` — script, audio_url, duration, show_notes, status.
- `reviews` — decision (approve/reject/edit), reviewer, channel, timestamp.
- `publications` — what was published where and when.
- Newsletter subscribers live in Listmonk's own schema, not duplicated here.

### Sound-worker contract (pull-based)
- The VPS exposes an authenticated narration-job API: the worker calls `claim` to take the
  next pending job (script text + voice id), then `complete` to upload the synthesized audio.
- Connection is **outbound from home only** (HTTPS to the VPS); the home box opens no inbound
  ports. (Alternative if synchronous calls are ever preferred: a Tailscale/WireGuard private
  link and a direct `POST /synthesize` — but pull-based is the default for resilience.)
- The **default voice is Tiago's cloned voice**, built from a reference sample (a few minutes
  of clean recorded speech) registered with the worker; other voices are optional.
- The worker uploads raw narration; the **assembly step** (intro/outro, loudness normalization,
  MP3 encode) runs in the VPS pipeline via ffmpeg, which then stores the file in object storage
  and records duration + URL on the episode. This keeps the home worker focused purely on GPU
  synthesis.

### Publishing flow
1. Ingest + extract + score → `topics` queue (scheduled) — on the VPS.
2. Operator/auto-selects a topic → generate blog + script + blurb → `drafts` — on the VPS.
3. VPS enqueues a narration job; the home sound-worker pulls it, synthesizes the cloned-voice
   narration, uploads it back; the VPS assembles (ffmpeg) → `episodes` with audio in storage.
4. Review dashboard shows blog + blurb + audio preview → per-channel approve.
5. Publishing writes blog markdown (rebuild Astro), updates podcast feed + episode page, and
   creates/sends a Listmonk campaign for the newsletter.

### Repository layout
`pipeline/`, `sound-worker/`, `web/` (Astro), `deploy/` (VPS `docker-compose.yml` + Listmonk
config + SMTP; plus a separate `compose.home.yml` for the GPU worker), `db/` (migrations).
Content markdown lives under `web/src/content/` using a date-based path similar to Akita's
`content/YYYY/MM/DD/`.

### Deployment topology (VPS + home GPU worker)
- **VPS (always-on, public).** Runs via Docker Compose: `pipeline`, `postgres`, object storage
  (`minio` or the provider's S3), `listmonk`, the review dashboard, and serves the built Astro
  site over TLS (Caddy/nginx). Has a real IP + domain, so no tunnel is needed. tiagovaccari.com
  and the audio enclosures are served from here (optionally fronted by a CDN).
- **Home computer (RTX 4060 Ti).** Runs only the `sound-worker` (and the private cloned-voice
  model/sample). It connects out to the VPS, claims narration jobs, and uploads results. No
  inbound ports, no static IP, sleeps freely — jobs queue on the VPS meanwhile.
- **Worker auth.** The worker authenticates to the VPS with a dedicated token over HTTPS; the
  reference voice sample and model never leave the home machine.

## Risks / Trade-offs

- **Polyglot ops.** Python + Astro + Listmonk is more moving parts than an all-TypeScript
  app. Accepted because the TTS/AI core forces Python regardless; Docker Compose contains the
  complexity on the VPS, and the home worker is a single small process.
- **Home worker availability.** The GPU sits on a home PC that may sleep, reboot, or change IP.
  Because the public site, DB, and newsletter all live on the always-on VPS, none of that
  affects visitors or sending — only podcast audio is delayed. Mitigation: pull-based jobs
  queue on the VPS and drain when the worker returns; a commercial TTS API stays a possible
  future fallback for time-sensitive episodes (kept as a non-goal for now).
- **Home→VPS connectivity.** The worker needs reliable outbound HTTPS to the VPS. Mitigation:
  token-authenticated outbound connection with retry/backoff; optional Tailscale link if a
  private network is preferred over public HTTPS.
- **Voice-clone consent & misuse.** A cloned voice is sensitive. Mitigation: it clones only
  Tiago's own consented voice from a sample he provides; the reference sample and model stay
  on the home machine and are never uploaded to the VPS or exposed publicly.
- **AI quality / hallucination.** Generated content can be wrong or off-brand. Mitigation:
  source-grounded generation with citations + the mandatory human review gate before publish.
- **Deliverability & compliance.** Self-sending risks spam folders and LGPD/GDPR obligations.
  Mitigation: double opt-in, unsubscribe, data-deletion handling, and a reputable SMTP
  provider (SES) with proper SPF/DKIM/DMARC.
- **Source ToS / rate limits.** Scraping aggregators can hit limits or ToS issues. Mitigation:
  prefer official feeds/APIs, store only extracts needed for grounding, and always link back
  to originals.
- **Cold start.** Voice cloning quality and trend scoring need tuning. Mitigation: start with
  a good default voice and a simple score, iterate after the first real episodes.
