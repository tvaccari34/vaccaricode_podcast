# Deploying Vaccari's Code Podcast to a VPS

A complete, first-time, step-by-step walkthrough for running the whole platform on a single
Linux VPS with automatic HTTPS. When you finish, `https://YOURDOMAIN` serves the bilingual site,
the newsletter and review dashboard are live, and your home GPU can produce podcast audio.

> This is the hand-holding guide. [`DEPLOY.md`](DEPLOY.md) is the terser operations runbook and
> has extra detail on the newsletter ([`NEWSLETTER.md`](NEWSLETTER.md)), backups, and the content
> flow — reach for it once you're comfortable. Replace `YOURDOMAIN` everywhere below with your real
> domain (the repo's defaults use `tiagovaccari.com`).

---

## 0. How the pieces fit

```
  VPS (always-on, public)                          HOME PC (RTX 4060 Ti, optional)
  ─────────────────────────                        ───────────────────────────────
  Caddy (auto-TLS) ── public :80/:443              sound-worker (F5-TTS voice clone)
  Astro static site · Listmonk · dashboard         pulls narration jobs over HTTPS
  pipeline · narration-api · scheduler             → uploads finished MP3s back
  PostgreSQL · MinIO (object storage)              NO inbound ports at home
```

Everything public and stateful lives on the VPS. The home machine is **optional** and only needed
to generate the cloned-voice **Portuguese** audio; it makes outbound calls only. English audio is
uploaded manually through the dashboard, so you can launch without the home worker at all.

---

## 1. What you need before starting

| Requirement | Notes |
|---|---|
| **VPS** | Ubuntu 22.04/24.04, **2 vCPU / 4 GB RAM** minimum (8 GB comfortable), **40 GB+** disk. Ports **80** and **443** open. |
| **Domain** | e.g. `YOURDOMAIN`, with DNS you control. |
| **Gemini API key** | https://aistudio.google.com/apikey (content generation + translation). |
| **Email sending** | Amazon SES or Resend, with your sending domain verified (SPF/DKIM/DMARC). |
| **GitHub access** | The repo `tvaccari34/vaccaricode_podcast` is **private** — the VPS needs a deploy key or PAT (Step 3). |
| **(Optional) Home GPU** | NVIDIA GPU + [NVIDIA Container Toolkit] for Portuguese podcast audio. |

[NVIDIA Container Toolkit]: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

---

## 2. DNS records

Point these at your VPS's public IP **before** you start the stack — Caddy needs them resolving to
issue TLS certificates. `news` and `dashboard` are separate origins on purpose (Listmonk emits
absolute `/admin` redirects and can't live under a path; the dashboard gets its own auth origin).

| Type | Host | Value | Purpose |
|---|---|---|---|
| `A` | `@` (apex) | `<VPS_IP>` | the public site |
| `A` | `www` | `<VPS_IP>` | optional; redirect to apex |
| `A` | `dashboard` | `<VPS_IP>` | review dashboard (behind Basic Auth + TLS) |
| `A` | `news` | `<VPS_IP>` | Listmonk (only if you expose its admin publicly; otherwise skip and tunnel) |

Verify from your laptop: `dig +short YOURDOMAIN` (and `dashboard.YOURDOMAIN`) should return the VPS IP.

---

## 3. Provision the VPS

SSH in as root (or a sudo user) and install Docker + Compose:

```bash
# Docker Engine + Compose plugin (official convenience script)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER    # then log out / back in so `docker` works without sudo

# Basic firewall: allow SSH + HTTP + HTTPS only
sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw --force enable

docker --version && docker compose version   # sanity check
```

### Get the code (private repo)

Pick one:

**Option A — GitHub Personal Access Token (quickest):** create a fine-grained PAT with read access
to the repo, then:

```bash
git clone https://github.com/tvaccari34/vaccaricode_podcast.git /opt/vaccaricode
# paste the PAT as the password when prompted (username = your GitHub handle)
```

**Option B — deploy key (better for a server):**

```bash
ssh-keygen -t ed25519 -f ~/.ssh/vaccaricode_deploy -N ""
cat ~/.ssh/vaccaricode_deploy.pub
# → GitHub repo → Settings → Deploy keys → Add deploy key (read-only is enough)
GIT_SSH_COMMAND="ssh -i ~/.ssh/vaccaricode_deploy" \
  git clone git@github.com:tvaccari34/vaccaricode_podcast.git /opt/vaccaricode
```

```bash
cd /opt/vaccaricode
```

---

## 4. Configure secrets (`.env`)

`.env` is git-ignored and **never leaves the VPS**. Start from the template:

```bash
cp .env.example .env
nano .env
```

Fill in **production** values. Do **not** reuse any secret that was ever shared in chat or committed
anywhere — generate fresh ones. Handy generator: `openssl rand -base64 24`.

Set at minimum:

```ini
# Domain → bare domain triggers automatic HTTPS (NO http:// prefix in prod)
SITE_DOMAIN=YOURDOMAIN
PUBLIC_SITE_URL=https://YOURDOMAIN

# Dashboard behind Caddy (its own subdomain, auto-TLS + Basic Auth)
DASHBOARD_DOMAIN=dashboard.YOURDOMAIN
DASHBOARD_USER=tiago
DASHBOARD_PASSWORD=<fresh strong password>

# Postgres / MinIO — strong, unique
POSTGRES_PASSWORD=<fresh>
DATABASE_URL=postgresql://boosternews:<same as POSTGRES_PASSWORD>@postgres:5432/boosternews
MINIO_ROOT_PASSWORD=<fresh>
S3_SECRET_ACCESS_KEY=<same as MINIO_ROOT_PASSWORD>
S3_PUBLIC_BASE_URL=https://YOURDOMAIN/audio

# Gemini
GEMINI_API_KEY=<fresh key>

# Home worker shared secret (only if using the GPU worker)
WORKER_AUTH_TOKEN=<fresh long random>

# TTS engine for Portuguese audio (F5-TTS = better Brazilian accent)
TTS_ENGINE=f5
F5_CKPT_FILE=pt-br/model_last.safetensors
F5_VOCAB_FILE=
REFERENCE_SAMPLE_FILE=reference_pt.wav
```

You'll come back to fill the **Listmonk** (`LISTMONK_*`, `PUBLIC_LISTMONK_*`) and **SMTP** values
in Steps 6–7, once those services are initialized.

> ⚠️ **Rotate the dev secrets.** The Gemini key, Listmonk API token, and dashboard password used in
> local development were exposed during setup — prod must use brand-new values.

### Point Caddy's dashboard Basic Auth at your new password

The dashboard sits behind **two** layers of Basic Auth: the app itself (`DASHBOARD_PASSWORD`) and
Caddy in front. Caddy stores a **bcrypt hash** (not the plaintext) in `deploy/caddy/Caddyfile`.
Regenerate it for your new password and paste it in:

```bash
docker run --rm caddy:2 caddy hash-password --plaintext 'YOUR-NEW-DASHBOARD-PASSWORD'
# copy the $2a$... output, then edit deploy/caddy/Caddyfile:
#   basic_auth {
#       {$DASHBOARD_USER}  <paste the hash here>
#   }
nano deploy/caddy/Caddyfile
```

Keep `DASHBOARD_USER` identical in `.env` and as the Caddy username. (One browser prompt satisfies
both layers — Caddy forwards the credentials upstream.)

---

## 5. Bring up the stack

All prod commands use both the base compose file **and** the production overlay (which closes the
dev-only ports so nothing but Caddy is public). Define a shortcut for the session:

```bash
DC="docker compose --env-file .env -f deploy/docker-compose.yml -f deploy/compose.prod.yml"
```

Start data services and initialize schemas:

```bash
$DC up -d postgres minio                 # database + object storage
$DC build migrate && $DC run --rm migrate   # apply DB migrations (build first — separate image)
$DC run --rm listmonk ./listmonk --install --yes --idempotent --config /listmonk/config.toml
```

Then bring up everything else:

```bash
$DC --profile scheduler up -d            # caddy, listmonk, dashboard, pipeline, narration-api, scheduler…
```

Caddy will now request Let's Encrypt certificates for `YOURDOMAIN` and `dashboard.YOURDOMAIN`.
Watch it succeed:

```bash
$DC logs -f caddy      # look for "certificate obtained successfully"; Ctrl-C to stop tailing
```

---

## 6. Newsletter: Listmonk lists, API user, SMTP

Listmonk's admin isn't public (the prod overlay closes its port). Reach it over an SSH tunnel from
your laptop:

```bash
ssh -L 9000:localhost:9000 user@YOURDOMAIN
# then open http://localhost:9000  (admin user/pass = LISTMONK_ADMIN_* from .env)
```

In the Listmonk UI:

1. **Lists → create two lists** — one Portuguese, one English (the audiences are different
   countries). Note each list's **numeric ID** and its **public UUID**.
2. **Settings → API users → new** (name it `blog_api`) — copy the token.
3. **Settings → SMTP** — configure Amazon SES or Resend (host, port 587, credentials, `SMTP_FROM`).
   See [`NEWSLETTER.md`](NEWSLETTER.md) for SES/Resend specifics and DNS (SPF/DKIM/DMARC).

Put the values in `.env`:

```ini
LISTMONK_API_USER=blog_api
LISTMONK_API_TOKEN=<token from step 2>
LISTMONK_LIST_ID=<PT numeric id>
LISTMONK_LIST_ID_EN=<EN numeric id>
PUBLIC_LISTMONK_URL=https://news.YOURDOMAIN         # or the tunneled URL if not public
PUBLIC_LISTMONK_LIST_UUID=<PT uuid>
PUBLIC_LISTMONK_LIST_UUID_EN=<EN uuid>
```

Recreate the services that read these (the pipeline for campaigns, and the web build for the
subscribe forms):

```bash
$DC up -d pipeline narration-api dashboard
```

---

## 7. Generate content and build the site

```bash
# One-time smoke: discover → extract → generate a first batch of drafts
$DC run --rm pipeline python -m boosternews seed-sources
$DC run --rm pipeline python -m boosternews ingest --all
$DC run --rm pipeline python -m boosternews extract
$DC run --rm pipeline python -m boosternews generate     # pt-BR + English drafts + an episode
```

**Review & approve** in the dashboard — `https://dashboard.YOURDOMAIN` (browser will prompt for the
Basic Auth user/password). Approve the blog + newsletter per language; for the English episode,
download the script, record it, and upload the MP3 there.

Then publish and build the static site:

```bash
$DC run --rm pipeline python -m boosternews publish --all
$DC run --rm web-build      # renders the approved content into web/dist, which Caddy serves
```

Open `https://YOURDOMAIN` — the site is live with a valid certificate.

---

## 8. Verify

```bash
curl -sI https://YOURDOMAIN | head -1                      # 200, valid TLS
curl -sI https://YOURDOMAIN/en/ | head -1                  # English mirror → 200
curl -s  https://YOURDOMAIN/rss.xml | head -5              # blog feed
curl -s  https://YOURDOMAIN/podcast/feed.xml | head -5     # podcast feed (episodes with audio)
curl -sI https://dashboard.YOURDOMAIN | head -1            # 401 (auth required — good)
curl -sI -u tiago:PASS https://dashboard.YOURDOMAIN | head -1   # 200 with creds
```

Validate the podcast feed at https://podba.se/validate/ before submitting it anywhere.

---

## 9. (Optional) Home GPU sound-worker — Portuguese audio

On the **home machine** (NVIDIA GPU + Container Toolkit installed), clone the repo and create a
`.env` with just the worker bits:

```ini
VPS_API_URL=https://YOURDOMAIN/api
WORKER_AUTH_TOKEN=<same value as on the VPS>
WORKER_ID=home-4060ti
VOICE_ID=tiago
TTS_ENGINE=f5
F5_CKPT_FILE=pt-br/model_last.safetensors
F5_VOCAB_FILE=
```

Place your voice reference sample at `deploy/voice/reference.wav`, then:

```bash
docker compose -f deploy/compose.home.yml up -d
docker compose -f deploy/compose.home.yml logs -f sound-worker
```

The worker connects out to the VPS, claims Portuguese narration jobs, synthesizes in your cloned
voice, and uploads the MP3 back — no inbound ports at home.

> **Gotcha:** `compose.home.yml` mounts the reference at `/data/voice/reference.wav` (a fixed name).
> Your dev file is `reference_pt.wav`, so on the home machine either **rename it to `reference.wav`**
> or edit the `REFERENCE_SAMPLE_PATH` line in `compose.home.yml`. (English audio never uses the
> worker — you record and upload it manually via the dashboard.)

---

## 10. Automate the ongoing cycle

The **scheduler** (already started in Step 5) runs ingest/extract/publish on intervals. Generation
is **off by default** to control LLM spend — turn it on by setting an interval in `.env`:

```ini
SCHED_GENERATE_MINUTES=360    # generate a batch every 6h (0 = never; you run `generate` by hand)
```

Site rebuilds are a separate Node build, so drive them with cron on the VPS (publishing only writes
the DB; the build renders it):

```cron
*/5 * * * * cd /opt/vaccaricode && docker compose --env-file .env -f deploy/docker-compose.yml -f deploy/compose.prod.yml run --rm web-build
```

Every generated batch still waits for your approval in the dashboard before it can be published.

---

## 11. Submit the podcast (one-time)

Once at least one episode **with audio** is live and `https://YOURDOMAIN/podcast/feed.xml` validates:

- **Apple Podcasts:** https://podcastsconnect.apple.com → add a show → submit the feed URL.
- **Spotify:** https://podcasters.spotify.com → add your podcast → submit the same URL.

---

## 12. Operations

**Update / redeploy after new commits:**

```bash
cd /opt/vaccaricode && git pull
DC="docker compose --env-file .env -f deploy/docker-compose.yml -f deploy/compose.prod.yml"
$DC build && $DC run --rm migrate      # rebuild images + apply any new migrations
$DC --profile scheduler up -d          # recreate changed services
$DC run --rm web-build                 # rebuild the site
```

**Backups (schedule daily):**

```bash
$DC exec postgres pg_dump -U boosternews boosternews > backup-app.sql
$DC exec postgres pg_dump -U boosternews listmonk   > backup-listmonk.sql
# plus the MinIO `boosternews-audio` bucket (mc mirror, or use managed S3 with versioning)
```

**Logs / status:** `$DC ps` · `$DC logs -f <service>` (e.g. `caddy`, `pipeline`, `dashboard`).

---

## 13. Security checklist

- [ ] `.env` has **fresh** secrets — none reused from dev/chat/commits.
- [ ] `DASHBOARD_PASSWORD` set (non-empty) **and** the matching bcrypt hash is in the Caddyfile.
- [ ] Prod overlay (`compose.prod.yml`) in every command → MinIO/Listmonk/dashboard/Mailpit ports
      are **not** published publicly; reach them via SSH tunnel.
- [ ] Firewall allows only 22/80/443.
- [ ] Dashboard reachable **only** over HTTPS (never plain HTTP publicly).
- [ ] SES/Resend domain verified (SPF/DKIM/DMARC) so newsletters aren't spam-filtered.
- [ ] `WORKER_AUTH_TOKEN` identical on VPS and home, and long/random.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Caddy TLS fails / stuck | DNS must resolve to the VPS **before** Caddy starts; ports 80/443 open; check `$DC logs caddy`. |
| Dashboard returns 401 with correct creds | `DASHBOARD_USER` must match in `.env` and Caddyfile; regenerate the bcrypt hash for the exact password. |
| `migrate` runs stale SQL | It's a **separate image** — `$DC build migrate` before `run --rm migrate`. |
| Listmonk redirects to `/admin` and breaks | It only works at an origin **root** — use the `news.` subdomain or the SSH tunnel, not a path. |
| Podcast feed empty | The feed only includes episodes **with audio** — upload/generate audio first. |
| Home worker can't reach VPS | `VPS_API_URL=https://YOURDOMAIN/api`, token matches, and the VPS `narration-api` is up. |
