# boosternews

An automated content factory: it discovers trends in the IT / software-development space and
turns one news item into a **blog post**, a **newsletter** section, and a narrated **podcast**
episode — with a human review gate before anything publishes.

Brand: [tiagovaccari.com](https://tiagovaccari.com). Inspired by akitaonrails.com and the
themakitachronicles.com newsletter.

## Topology

| Where | Runs | Notes |
|-------|------|-------|
| **VPS** (always-on) | Astro site, pipeline, PostgreSQL, object storage (MinIO/S3), Listmonk, review dashboard | Public + stateful. Docker Compose. |
| **Home PC** (RTX 4060 Ti) | `sound-worker` only | Voice generation (XTTS-v2 cloned voice). Pulls jobs from the VPS over outbound HTTPS — no inbound ports, no static IP. |

If the home PC is offline, narration jobs queue on the VPS and drain when it returns; the
public site is unaffected.

## Repository layout

```
pipeline/       Python: trend discovery, AI generation, audio assembly, publishing (runs on VPS)
sound-worker/   Python: home GPU worker that synthesizes narration in the cloned voice
web/            Astro static site (blog, podcast, about, subscribe) — scaffolded in task group 6
db/             SQL migrations + migration runner
deploy/         Docker Compose (VPS + home), Caddy, Listmonk config
openspec/       The spec-driven proposal (change: bootstrap-content-platform)
```

## Stack

- **Pipeline / worker:** Python 3.12 (feedparser, trafilatura, Google Gemini `google-genai`, boto3, psycopg, ffmpeg)
- **Site:** Astro (static) — RSS + iTunes podcast feed
- **Newsletter:** self-hosted Listmonk, pluggable SMTP (Amazon SES or Resend)
- **TTS:** XTTS-v2 (zero-shot voice cloning) on the home GPU
- **Data:** PostgreSQL + S3-compatible object storage

## Quick start (VPS / dev)

Run from the **repo root** so the single root `.env` feeds both Compose interpolation and the
containers (a `Makefile` wraps the flags):

```bash
cp .env.example .env          # then fill in the required secrets
make up-infra                 # postgres + minio
make migrate                  # create the schema
make up                       # pipeline, listmonk, caddy
make logs                     # follow pipeline output
```

Without `make`, pass the env file and compose file explicitly:

```bash
docker compose --env-file .env -f deploy/docker-compose.yml up -d
```

On the home PC:

```bash
cp .env.example .env          # set VPS_API_URL + WORKER_AUTH_TOKEN (token must match the VPS)
make home-up                  # or: docker compose --env-file .env -f deploy/compose.home.yml up -d
```

See `deploy/DEPLOY.md` for the full deployment & operations runbook, `deploy/NEWSLETTER.md` for
the Listmonk/opt-in setup, and `openspec/changes/bootstrap-content-platform/` for the design.

## Status

Working end-to-end locally: **trend → AI draft (blog/script/newsletter) → human review/approve →
publish → live on the site + newsletter delivered**, on a schedule.

| Done | Pending |
|------|---------|
| Infra, trend discovery, content generation (Gemini), review dashboard, Astro site, newsletter (Listmonk), publishing, scheduler | Podcast audio (sound-worker, needs home GPU); VPS deploy with DNS/TLS |

Progress is tracked in `openspec/changes/bootstrap-content-platform/tasks.md`.

## Manual authoring

Besides the automated trend→AI pipeline, you can hand-write content from the review dashboard:
**Create Post** (blog + optional newsletter) and **Create Episode** (script + show notes), in
pt-BR and/or English. Manual entries create a synthetic `origin='manual'` topic and flow through
the same review → approve → publish → site/feed path; the automated pipeline skips manual topics,
so both modes coexist. pt-BR episodes can be auto-narrated by the home GPU worker; English audio is
uploaded manually. See `openspec/changes/manual-content-authoring/`.

## Managing content

The dashboard's **Manage content** view (`/manage`) lists all blog posts and podcast episodes
(pt-BR + English) — automated or manual, published or not — with per-item actions: **publish,
unpublish, edit, replace/regenerate audio, and delete** (deleting an episode also purges its
stored audio). Changes are DB-only and appear on the live site within ~1 minute: each action (and
a **Rebuild now** button) queues a row in `site_build_requests`, which a 1-minute host watcher
(`deploy/rebuild-watch.sh`) consumes to rebuild the static site. See
`openspec/changes/content-management/`.
