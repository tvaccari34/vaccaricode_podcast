## Why

There's no visibility into the **website**: which posts/episodes draw readers, where visitors come
from, or whether the newsletter/podcast links actually convert. OP3 (PR #22) covers podcast
*downloads*, but nothing measures the site itself.

Add **privacy-friendly, self-hosted web analytics (Umami)** that reuses the existing infrastructure,
plus a **UTM convention** so traffic from the newsletter, podcast show notes, and social is
attributable to its source. Umami is chosen over Plausible because it **reuses the shared Postgres**
(Plausible's self-hosted edition needs an extra ClickHouse service — heavier on this box), is
cookieless/LGPD-friendly (no consent banner), and is fully free self-hosted.

## What Changes

- **Deploy Umami** as a Swarm service in the boosternews stack, reusing the shared
  `postgres_postgres` (a new `umami` database) behind Traefik at **`umami.tiagovaccari.com`**.
- **Add the Umami tracker** to the Astro `Base` layout, **gated on config** so dev/local builds stay
  clean and analytics can be turned off by unsetting one variable.
- **Widen the CSP** (`bn-csp`) to allow the Umami origin in `script-src` + `connect-src` — required,
  or the tracker is silently blocked. Nothing else is loosened.
- Define a **UTM convention** (a small `utm_source` / `utm_medium` / `utm_campaign` taxonomy) and have
  the pipeline **append UTM params to the links it delivers through external channels** (newsletter
  email, podcast show notes) that point back to the site. Umami captures `utm_*` automatically.
- Add a short **privacy note** to the site (anonymous, cookieless analytics).

## Capabilities

### New Capabilities
- `site-analytics`: privacy-friendly self-hosted web analytics with traffic-source attribution via a
  UTM convention.

## Impact

- **New Umami service** + Traefik route + a `umami` DB on the shared Postgres; `.env` config
  (`UMAMI_*` secrets + `PUBLIC_UMAMI_*` for the tracker).
- **`web/src/layouts/Base.astro`** — config-gated tracker snippet; **CSP middleware** in
  `deploy/stack.boosternews.yml`.
- **`pipeline`** — a `with_utm()` helper + UTM tagging of newsletter/show-notes CTA links, + config.
- **Docs** — deploy Umami, create the site → website-id, the UTM taxonomy table.
- **Not** behind Basic Auth: the tracker/collection endpoints (`/script.js`, `/api/send`) must stay
  public; Umami's own login guards the dashboard (contrast with the Listmonk admin lockdown).
- Reversible: unset `PUBLIC_UMAMI_WEBSITE_ID` (tracker not emitted) + drop the CSP origin.
