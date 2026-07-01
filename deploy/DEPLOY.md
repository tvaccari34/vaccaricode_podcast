# boosternews — deployment & operations runbook

End-to-end guide: secrets, the content flow, the scheduler, and production deployment.

> **First time deploying to a VPS?** Follow the step-by-step [`VPS_DEPLOY.md`](VPS_DEPLOY.md)
> (VPS provisioning, DNS, private-repo access, secret rotation, TLS). This file is the terser
> operations reference for when you already know the layout.

## Architecture

```
  VPS (always-on, public)                         HOME PC (RTX 4060 Ti)
  pipeline · scheduler · PostgreSQL · MinIO        sound-worker (XTTS-v2)
  Listmonk · review dashboard · Astro site         pulls narration jobs (outbound HTTPS)
        served by Caddy (auto-TLS)
```

Everything public/stateful runs on the VPS via Docker Compose. The home machine runs only the
GPU sound-worker, which pulls narration jobs from the VPS — no inbound ports at home.

## 1. Prerequisites

- A VPS with Docker + Docker Compose, a domain (e.g. `tiagovaccari.com`) with an **A record** to
  the VPS IP, and ports 80/443 open.
- A Google **Gemini API key** (https://aistudio.google.com/apikey).
- A transactional email provider (**Amazon SES** or **Resend**) with the sending domain verified.
- (Podcast audio) a home machine with an NVIDIA GPU — see task group 4 / `sound-worker/`.

## 2. Secrets (`.env`)

Copy `.env.example` → `.env` and fill in. Required (the pipeline fails fast if missing):
`DATABASE_URL`, `GEMINI_API_KEY`, `S3_*`, `WORKER_AUTH_TOKEN`. For production also set:
`SITE_DOMAIN=tiagovaccari.com`, `PUBLIC_SITE_URL=https://tiagovaccari.com`, the Listmonk API
creds (`LISTMONK_API_USER/TOKEN/LIST_ID`, `PUBLIC_LISTMONK_LIST_UUID`), and real SMTP. Keep `.env`
out of git (it is git-ignored).

## 3. The content flow

```
seed-sources → ingest → extract → generate → [review/approve] → publish → web-build → live
```

| Step | Command |
|------|---------|
| Seed trend sources | `… run --rm pipeline python -m boosternews seed-sources` |
| Discover trends | `… run --rm pipeline python -m boosternews ingest --all` |
| Extract article text | `… run --rm pipeline python -m boosternews extract` |
| Generate drafts | `… run --rm pipeline python -m boosternews generate` |
| **Review & approve** | review dashboard → http://localhost:8080/ |
| Publish approved | `make publish` (publish + web-build) |

`…` = `docker compose --env-file .env -f deploy/docker-compose.yml`.

## 4. Scheduler (automated cycle)

The scheduler runs ingest / extract / (optional) generate / publish on intervals, each job
isolated and retried on its next tick. Intervals are env-configurable (`SCHED_*_MINUTES`;
`0` disables a job — `SCHED_GENERATE_MINUTES` defaults to 0 to control LLM spend).

```bash
make scheduler        # docker compose --profile scheduler up -d scheduler
make scheduler-logs
```

**Site rebuild** is a separate Node build, so schedule it with cron on the VPS (publishing only
updates the DB; the rebuild renders it):

```cron
*/5 * * * * cd /opt/boosternews && docker compose --env-file .env -f deploy/docker-compose.yml run --rm web-build
```

## 5. Production deployment

```bash
git clone <repo> /opt/boosternews && cd /opt/boosternews
cp .env.example .env            # fill in prod secrets; SITE_DOMAIN=tiagovaccari.com
DC="docker compose --env-file .env -f deploy/docker-compose.yml -f deploy/compose.prod.yml"

$DC up -d postgres minio
$DC run --rm migrate
$DC run --rm listmonk ./listmonk --install --yes --idempotent --config /listmonk/config.toml
$DC --profile scheduler up -d        # all services incl. scheduler
$DC run --rm web-build               # first site build
```

- **TLS:** Caddy auto-provisions a certificate once `SITE_DOMAIN` is the real domain pointed at
  the host. No manual certs.
- **`compose.prod.yml`** closes the dev-only published ports (MinIO console, Listmonk, dashboard,
  Mailpit). Reach them via SSH tunnel/VPN.
- **Dashboard security (defense in depth).** Three layers:
  1. **App Basic Auth** built into the dashboard — set a strong `DASHBOARD_PASSWORD` (empty = auth
     disabled, dev only; the app logs a warning).
  2. **Caddy in front** on its own origin (`DASHBOARD_DOMAIN`, e.g. `dashboard.tiagovaccari.com`)
     with its own `basic_auth` block and **automatic HTTPS** — so credentials are never sent in the
     clear. Caddy forwards the `Authorization` header upstream, so one browser prompt satisfies both
     layers. The bcrypt password hash lives in `deploy/caddy/Caddyfile`; regenerate it after a
     password change with `docker run --rm caddy:2 caddy hash-password --plaintext 'PASS'` and keep
     `DASHBOARD_USER` in sync.
  3. **Closed dev port** — `compose.prod.yml` closes the direct `:8080` publish, so the only way in
     is through Caddy over HTTPS. Never expose the dashboard on plain HTTP publicly.

  Dev: reach it at `http://dashboard.localhost/` (add `127.0.0.1 dashboard.localhost` to your hosts
  file if your resolver doesn't already map `*.localhost`).
- **Email:** point Listmonk at SES/Resend and verify SPF/DKIM/DMARC — see
  [NEWSLETTER.md](NEWSLETTER.md). Create the Listmonk API user and set `LISTMONK_API_TOKEN`.

## 6. Home GPU sound-worker (podcast audio)

On the home machine (NVIDIA Container Toolkit installed):

```bash
cp .env.example .env            # set VPS_API_URL=https://tiagovaccari.com/api + WORKER_AUTH_TOKEN
# place the voice reference sample at deploy/voice/reference.wav
docker compose --env-file .env -f deploy/compose.home.yml up -d
```

It connects out to the VPS, claims narration jobs, synthesizes in the cloned voice, and uploads
audio back. (Synthesis itself is task group 4.)

## 7. Submit the podcast to directories (one-time)

Once at least one episode with audio is published and `https://tiagovaccari.com/podcast/feed.xml`
is reachable:

- **Apple Podcasts:** https://podcastsconnect.apple.com → add a show → submit the feed URL.
- **Spotify:** https://podcasters.spotify.com → add your podcast → submit the same feed URL.

Validate the feed first at https://podba.se/validate/ or castfeedvalidator.com.

## 8. Smoke test

After deploy, confirm the loop:

1. `… run --rm pipeline python -m boosternews check` → config + Postgres + storage OK.
2. `… run --rm pipeline python -m boosternews seed-sources && … ingest --all && … extract`.
3. `… run --rm pipeline python -m boosternews generate` → 3 drafts + an episode.
4. Dashboard → approve blog + newsletter.
5. `make publish` → blog published; newsletter campaign created.
6. `https://tiagovaccari.com/blog` shows the post; `/rss.xml` and `/podcast/feed.xml` are valid.
7. Subscribe on `/subscribe` → confirmation email → confirm → start the campaign in Listmonk.

## 9. Backups

- **PostgreSQL:** `docker compose exec postgres pg_dump -U boosternews boosternews > backup.sql`
  (and the `listmonk` DB). Schedule daily.
- **Object storage:** back up the MinIO `boosternews-audio` bucket (or use a managed S3 with
  versioning).
