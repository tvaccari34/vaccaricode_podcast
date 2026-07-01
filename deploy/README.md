# deploy

Docker Compose for both locations.

- `docker-compose.yml` — **VPS** stack: postgres, minio, migrate (one-shot), pipeline, listmonk, caddy.
- `compose.home.yml` — **home PC** stack: the GPU sound-worker only.
- `caddy/Caddyfile` — TLS + static site + `/newsletter/*` proxy to Listmonk.
- `listmonk/config.toml` — Listmonk base config (SMTP is configured in its UI; pluggable SES/Resend).
- `postgres/initdb/` — first-boot script that creates the separate Listmonk database.

## VPS bring-up

Run from the **repo root** (not `deploy/`) so the root `.env` feeds both Compose `${VAR}`
interpolation and the containers. The `Makefile` wraps the flags; explicit commands shown too.

```bash
cp .env.example .env              # fill in required secrets (see fail-fast vars)

make up-infra                     # docker compose --env-file .env -f deploy/docker-compose.yml up -d postgres minio
make migrate                      # apply db/migrations → schema_migrations
make listmonk-install             # first run only: initialize Listmonk's tables
make up                           # pipeline, listmonk, caddy
make logs                         # pipeline prints "configuration loaded OK" + reachability
```

> Running `docker compose` from inside `deploy/` will emit “variable is not set” warnings,
> because Compose looks for `.env` next to the compose file. Use the root `.env` via
> `--env-file .env` (what the Makefile does).

### Local dev access (with the provided dev `.env`)

| Service | URL | Notes |
|---------|-----|-------|
| Placeholder site | http://localhost/ | Astro build replaces it in task group 6 |
| Review dashboard | http://localhost:8080/ | Approve/reject drafts per channel |
| Listmonk admin | http://localhost:9000/ | Auto-provisioned admin (`LISTMONK_ADMIN_*` in `.env`) |
| Mailpit (dev mail) | http://localhost:8025/ | Catches opt-in/campaign emails locally |
| MinIO console | http://localhost:9001/ | Login = `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |

See [NEWSLETTER.md](NEWSLETTER.md) for the Listmonk/SMTP/opt-in runbook.

> Listmonk is served on its own port (9000), not under `/newsletter/`, because it only works at
> an origin root. In production give it a subdomain (e.g. `news.tiagovaccari.com`).

`SITE_DOMAIN=http://localhost` in the dev `.env` makes Caddy serve plain HTTP locally. In
production set a bare domain (e.g. `tiagovaccari.com`) and Caddy provisions HTTPS automatically.

The MinIO console is on `:9001` (remove the port mapping in production). The audio bucket is
created automatically by the pipeline's storage helper (`ensure_bucket`).

## Home worker bring-up

On the home machine (NVIDIA Container Toolkit installed), from the repo root:

```bash
cp .env.example .env              # set VPS_API_URL + WORKER_AUTH_TOKEN (token must match the VPS)
# Place the private voice reference sample at deploy/voice/reference.wav (git-ignored).
make home-up                      # docker compose --env-file .env -f deploy/compose.home.yml up -d
make home-logs
```

## Notes

- **Secrets**: everything comes from `../.env`; the pipeline fails fast if a required var is missing.
- **Pluggable SMTP**: add SES and Resend as two SMTP servers in Listmonk and enable one to switch.
- **TLS**: Caddy auto-provisions certificates when `SITE_DOMAIN` is a real domain pointed at the VPS.
- The home worker makes **outbound** calls only — no inbound ports, no port-forwarding.
