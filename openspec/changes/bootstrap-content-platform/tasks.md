## 1. Project scaffolding & infrastructure

- [x] 1.1 Create repo layout: `pipeline/`, `sound-worker/`, `web/`, `deploy/`, `db/`
- [x] 1.2 Add `deploy/docker-compose.yml` for the VPS backend: pipeline, postgres, minio (object storage), listmonk, review dashboard (placeholder), and a TLS reverse proxy (Caddy) serving the Astro build
- [x] 1.3 Add `deploy/compose.home.yml` for the home GPU sound-worker (NVIDIA runtime) — outbound-only, no published ports
- [x] 1.4 Define `.env`/secrets handling (Gemini API key, SMTP creds, storage keys, worker auth token); fail-fast on missing required secrets
- [x] 1.5 Provision PostgreSQL and write initial migrations for `sources`, `topics`, `drafts`, `episodes`, `reviews`, `publications`, and a `narration_jobs` queue
- [x] 1.6 Provision MinIO (S3-compatible) bucket for audio and a storage client helper

## 2. Trend discovery (`trend-discovery`)

- [x] 2.1 Implement source registry + config (RSS/Atom, Hacker News, GitHub Trending)
- [x] 2.2 Implement scheduled ingestion job (per-source fetch, error isolation, persist raw candidates)
- [x] 2.3 Integrate `trafilatura` article extraction; store cleaned text on each candidate
- [x] 2.4 Implement dedup (merge same story across sources) and a relevance score; order the candidate queue
- [x] 2.5 Tests for ingestion, extraction, dedup, and scoring

## 3. Content generation (`content-generation`)

- [x] 3.1 Integrate Google Gemini (google-genai SDK, gemini-2.5-flash) via boosternews.llm with configurable brand voice
- [x] 3.2 Implement blog-post generation (markdown + frontmatter) grounded in sources with citations
- [x] 3.3 Implement podcast-script generation grounded in sources
- [x] 3.4 Implement newsletter-blurb generation; link all three drafts to the same topic
- [x] 3.5 Apply per-format length/tone/structure constraints; tests for grounding and attribution

## 4. Sound-worker & podcast production (`podcast-production`)

- [x] 4.1 VPS-side narration-job API (FastAPI: claim / complete / fail, token-auth) — verified live
- [x] 4.2 Home GPU sound-worker loop: claim → synthesize → upload, outbound-only HTTPS, retry/backoff
- [x] 4.3 XTTS-v2 zero-shot voice cloning — VERIFIED LIVE on the RTX 4060 Ti: real reference.wav → 7-min narration of an episode in the owner's cloned voice, published to the site
- [x] 4.4 VPS-side audio assembly via ffmpeg: optional intro/outro, loudness normalization, MP3 encode — verified
- [x] 4.5 Upload episode audio to object storage; record duration, size, URL on the episode — verified (audio served public, podcast feed enclosure)
- [x] 4.6 Worker-offline (jobs stay queued) + synthesis-failure requeue/fail; tests for job lifecycle — verified end-to-end with a stand-in worker

## 5. Review workflow (`review-workflow`)

- [x] 5.1 Implement review dashboard showing blog text, newsletter blurb, and an audio preview
- [x] 5.2 Implement per-channel approve/reject/request-edit, recording reviewer + timestamp
- [x] 5.3 Enforce the approval gate: nothing is publishable without approval for its channel
- [x] 5.4 Tests for state transitions and the publish gate

## 6. Website (`website`)

- [x] 6.1 Scaffold Astro site (queries Postgres at build time, per decision — not file-based collections)
- [x] 6.2 Build blog list/detail pages and podcast episode pages with an audio player + show notes
- [x] 6.3 Build the about/bio page (Tiago Vaccari: Sr SWE leading AI initiatives, 20+ yrs, BR origin, UK→US 2023; GitHub link)
- [x] 6.4 Build the themed newsletter subscribe page wired to Listmonk; light/dark theme toggle
- [x] 6.5 Generate blog RSS feed and the iTunes-compatible podcast feed

## 7. Newsletter (`newsletter-subscription`)

- [x] 7.1 Deploy and configure Listmonk (auto-provisioned admin, public double-opt-in list)
- [x] 7.2 Pluggable SMTP in Listmonk (named Mailpit/SES/Resend servers, switch by toggling enabled); SPF/DKIM/DMARC documented for prod (deploy-time DNS)
- [x] 7.3 Wire subscribe page → Listmonk opt-in; unsubscribe (built-in) + LGPD data export/wipe enabled
- [x] 7.4 Verify double opt-in confirmation (live via Mailpit); delivery/open analytics available per campaign once SMTP+API token set

## 8. Publishing (`publishing`)

- [x] 8.1 Publish approved blog (gate-enforced status→published) and trigger site rebuild (web-build)
- [x] 8.2 Publish approved episodes: status→published; episode page + podcast feed regenerate (audio URL when produced)
- [x] 8.3 Create approved newsletter editions as Listmonk campaigns (send pending Listmonk SMTP config — task group 7)
- [x] 8.4 Regenerate RSS/podcast feeds on rebuild; blog and podcast for a shared topic cross-link

## 9. Orchestration, deployment & docs

- [x] 9.1 Implement scheduled/queued job orchestration with retry (boosternews.scheduler: ingest/extract/generate/publish, per-job isolation+retry; `scheduler` service + `make scheduler`)
- [~] 9.2 VPS deploy: compose.prod.yml (closes dev ports) + Caddy auto-TLS + DEPLOY.md runbook (DNS/TLS steps documented; execution needs the VPS/domain). Home sound-worker hook documented (synthesis = group 4)
- [~] 9.3 Submit podcast feed to Apple Podcasts / Spotify — documented one-time step (needs published audio + public feed)
- [x] 9.4 Write deployment runbook (deploy/DEPLOY.md) + NEWSLETTER.md: setup, secrets, pipeline, review-to-publish, scheduler, smoke test
- [x] 9.5 End-to-end smoke test verified: 7 services healthy, trend→draft→approve→publish→live + newsletter delivered; site + feeds 200
