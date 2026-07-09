# Design — site analytics (Umami) + UTM convention

## Context

The site is a static Astro build served by nginx behind Traefik. The stack already runs Listmonk by
reusing the shared `postgres_postgres` with a dedicated DB and a Traefik subdomain — the same pattern
fits Umami. A strict CSP (`bn-csp`) was added recently: `script-src 'self' 'unsafe-inline'` and
`connect-src 'self'`, which will block any third-party analytics tracker unless widened. The web build
runs via `deploy/publish-rebuild.sh` (`node:22-alpine … npm run build` with `--env-file .env`), so
`PUBLIC_*` env vars are available to Astro at build time (`import.meta.env.PUBLIC_*`).

## Goals

- Self-hosted, privacy-friendly web analytics reusing existing infra (no new DB engine).
- Tracker opt-in by config; off by default in dev; one-variable kill switch.
- Attribute traffic to source (newsletter / podcast / social) via a documented UTM convention.
- Keep the CSP strict except for the single Umami origin.

## Non-Goals

- Product analytics / funnels / session replay; user-level tracking or PII.
- Cross-device identity. Cookie-based tracking (Umami is cookieless by design).
- Replacing OP3 (that stays for podcast *download* stats; this is *site* traffic).

## Key decisions

### 1. Umami, not Plausible
Umami = one Node container + a Postgres DB, which the shared `postgres_postgres` already provides.
Plausible's self-hosted edition additionally requires **ClickHouse** (a columnar DB, ~0.5 GB+ RAM) —
unjustified weight on an already-loaded box. Both are cookieless/GDPR-friendly; Umami wins on fit.

### 2. Deployment topology (mirror Listmonk)
A `umami` service on `BoosterBot_Network`, image `ghcr.io/umami-software/umami:postgresql-latest`,
`DATABASE_URL=postgresql://umami:…@postgres_postgres:5432/umami`, a generated `APP_SECRET`. Traefik
router `Host(umami.tiagovaccari.com)` → port `3000`, TLS via `letsencryptresolver`, with
`bn-sec-headers` applied. A `umami` DB + role is created once on the shared Postgres; Umami runs its
own schema migrations on boot.

### 3. Tracker endpoints stay PUBLIC (no Basic Auth)
Web analytics works by the public site loading `…/script.js` and POSTing pageviews to `…/api/send`.
So — unlike the Listmonk admin — the Umami router must **not** sit behind Basic Auth; that would break
collection. Umami ships its own login (admin user + password) which guards the dashboard UI and its
authenticated API. So: dashboard = Umami login; collection = public by design.

### 4. Config-gated tracker in `Base.astro`
Inject into `<head>`, emitted only when a website id is configured:
```astro
{import.meta.env.PUBLIC_UMAMI_WEBSITE_ID && (
  <script defer src={import.meta.env.PUBLIC_UMAMI_SRC} data-website-id={import.meta.env.PUBLIC_UMAMI_WEBSITE_ID}></script>
)}
```
- `PUBLIC_UMAMI_SRC` = `https://umami.tiagovaccari.com/script.js`
- `PUBLIC_UMAMI_WEBSITE_ID` = the id Umami mints when the site is created in its dashboard.
These aren't secrets (they appear in page source). Dev builds omit both → no tracker.

### 5. Two-phase rollout (chicken-and-egg)
The website id only exists after Umami is up. So: **(a)** deploy Umami + create the admin login + add
the website (`tiagovaccari.com`) → copy its website id; **(b)** set `PUBLIC_UMAMI_*` + widen the CSP +
rebuild the site. Documented as two steps in DEPLOY.

### 6. CSP widening (required)
Add `https://umami.tiagovaccari.com` to `script-src` and `connect-src` in `bn-csp`. Everything else
stays as-is. `bn-csp` is shared by `bn-web` and `bn-dashboard`; only the public site carries the
tracker, but adding the origin to the shared middleware is harmless.

### 7. UTM convention — tag only externally-delivered links
Internal on-site links (e.g. the blog's own subscribe CTA) must **not** be UTM-tagged — that pollutes
Umami with self-referral "campaigns" for ordinary navigation. Tag only links that reach the user
through an **external channel** and point back to the site:

| Channel | `utm_source` | `utm_medium` | `utm_campaign` |
|---|---|---|---|
| Weekly newsletter (email) | `newsletter` | `email` | `weekly-digest-<YYYY-Www>` |
| Podcast show notes | `podcast` | `podcast` | `episode-<topic_id>` |
| Social posts (manual) | `x` / `linkedin` / `github` | `social` | free-form |

A pure helper `with_utm(url, *, source, medium, campaign)` appends the params (idempotent, preserves
existing query). Applied in the pipeline where those links are generated: the **newsletter digest**
body links (in `digest.py`) and the **podcast show-notes** subscribe CTA (in `generate.py`). The
blog's on-site CTA stays untagged. Umami reads `utm_*` off the landing URL automatically.

### 8. Privacy / LGPD
Umami is cookieless and stores no PII (hashed, salted, per-day non-identifying visitor counts) → no
consent banner required. Add one line to the site's privacy/about copy: "anonymous, cookieless
analytics (Umami), no personal data or cross-site tracking."

## Config
```
# secrets (.env, gitignored)
UMAMI_DB_PASSWORD=…
UMAMI_APP_SECRET=…              # random 32+ chars
# public (baked into the static build; not secret)
PUBLIC_UMAMI_SRC=https://umami.tiagovaccari.com/script.js
PUBLIC_UMAMI_WEBSITE_ID=        # from the Umami dashboard after step (a)
# pipeline UTM (optional; sensible defaults)
UTM_ENABLED=true
```

## Rollout / reversibility
Two-phase as in §5. Kill switch: unset `PUBLIC_UMAMI_WEBSITE_ID` and rebuild → no tracker; optionally
drop the CSP origin. The Umami service + data can remain or be removed independently.

## Risks / trade-offs
- **Ad-blockers** block some third-party analytics by hostname; a first-party subdomain
  (`umami.tiagovaccari.com`) is blocked less than `umami.is`, but some undercount remains — acceptable
  for trend-level insight.
- **CSP mistakes** silently disable tracking — verification step drives a real pageview and checks for
  CSP violations.
- **UTM over-tagging** distorts sources — mitigated by tagging only externally-delivered links (§7).

## Alternatives considered
- **Plausible CE** — rejected: ClickHouse overhead (§1).
- **GoatCounter / server-log analytics** — lighter, but weaker UI and no UTM/campaign breakdown.
- **Basic-Auth the whole Umami host** — rejected: breaks the public collection endpoints (§3).
